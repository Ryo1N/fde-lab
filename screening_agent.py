"""
Lab 16: Handoffs - Multi-Agent Interview System

This module implements a multi-agent interview system where:
- Orchestrator Agent extracts skills and manages the interview flow
- Skills Evaluator Agent asks questions and evaluates answers
- Both agents hand off to each other using the Agents SDK handoff mechanism

Architecture:
- Agents SDK for agent orchestration and handoffs
- LangChain for check_answer tool
"""

import random
from typing import Literal, Optional
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# LangChain imports for check_answer
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Agents SDK imports
from config import settings
from agents import Agent, Runner, function_tool, set_default_openai_key, SQLiteSession
from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX
from models import JobPost

# ==============================================================================
# DATABASE HELPERS
# ==============================================================================

def get_db_session():
    """Create and return a SQLAlchemy session for database operations"""
    engine = create_engine(str(settings.DATABASE_URL))
    Session = sessionmaker(bind=engine)
    return Session()


# Internal state for interview sessions
interview_state = {
    "session123": {
        "skills": [],
        "evaluation": []  # list of tuples (Skill, True/False)
    }
}

# ==============================================================================
# QUESTION BANK (Lab 15)
# ==============================================================================

question_bank = {
    "python": {
        "easy": [
            "If `d` is a dictionary, then what does `d['name'] = 'Siddharta'` do?",
            "if `l1` is a list and `l2` is a list, then what is `l1 + l2`?",
        ],
        "medium": [
            "How do you remove a key from a dictionary?",
            "How do you reverse a list in python?"
        ],
        "hard": [
            "If `d` is a dictionary, then what does `d.get('name', 'unknown')` do?",
            "What is the name of the `@` operator (Example `a @ b`) in Python?"
        ]
    },
    "sql": {
        "easy": [
            "What does LIMIT 1 do at the end of a SQL statement?",
            "Explain this SQL: SELECT product_name FROM products WHERE cost < 500"
        ],
        "medium": [
            "What is a view in SQL?",
            "How do we find the number of records in a table called `products`?"
        ],
        "hard": [
            "What is the difference between WHERE and HAVING in SQL?",
            "Name a window function in SQL"
        ]
    },
    "system design": {
        "easy": [
            "Give one reason where you would prefer a SQL database over a Vector database",
            "RAG requires a vector database. True or False?"
        ],
        "medium": [
            "Give one advantage and one disadvantage of chaining multiple prompts?",
            "Mention three reasons why we may not want to use the most powerful model?"
        ],
        "hard": [
            "Mention ways to speed up retrieval from a vector database",
            "Give an overview of Cost - Accuracy - Latency tradeoffs in an AI system"
        ]
    }
}

# ==============================================================================
# PYDANTIC MODELS FOR STRUCTURED OUTPUT
# ==============================================================================

class ExtractedSkills(BaseModel):
    """Structured output for skill extraction"""
    skills: list[str] = Field(description="List of technical skills extracted from job description")


class ValidationResult(BaseModel):
    """Structured output for answer validation"""
    correct: bool
    reasoning: str

# ==============================================================================
# PROMPTS
# ==============================================================================

# Lab 15: Validation prompt for check_answer (LangChain)
VALIDATION_PROMPT = """
Evaluate the given interview answer.

# Instructions

Provide a JSON response with:
- correct: true or false depending if the answer was correct or not for the given question in the context of the given skill.
- reasoning: brief explanation (2-3 sentences)

For subjective answers, mark the answer true if the majority of the important points have been mentioned.

Answers are expected to be brief, so be rigorous but fair. Look for technical accuracy and clarity.

# Output Format

{format_instructions}

# Task

Skill: {skill}
Question: {question}
Answer:
{answer}

Evaluation:"""

# Lab 16: Orchestrator prompt with RECOMMENDED_PROMPT_PREFIX
ORCHESTRATOR_SYSTEM_PROMPT = """
{RECOMMENDED_PROMPT_PREFIX}

You are an interview orchestrator. Your goal is to evaluate the candidate on the required skills.

# INSTRUCTIONS

Follow the following steps exactly:

1. Extract key skills from the job description using extract_skills tool
2. Welcome the candidate, explain the screening process and ask if they are ready
3. Use get_next_skill_to_evaluate tool to get the next skill
4. If skill is not None: hand off to "Skills Evaluator Agent" with the skill name
5. When Evaluator returns with result, use update_evaluation to save it
6. REPEAT steps 3-5 until get_next_skill_to_evaluate returns None
7. When all skills are done, return {"status": "done"}

IMPORTANT: Keep looping through steps 3-5 until ALL skills are evaluated.
"""

ORCHESTRATOR_USER_PROMPT = """
Start an interview for the following values:

session_id: {session_id}
job_id: {job_id}

Begin by welcoming the applicant, extracting the key skills, then evaluate each one.
"""

# Lab 16: Evaluation prompt with RECOMMENDED_PROMPT_PREFIX
EVALUATION_SYSTEM_PROMPT = """
{RECOMMENDED_PROMPT_PREFIX}

You are a specialised skill evaluator. Your job is to evaluate the candidate's proficiency in a given skill.

# INSTRUCTIONS

1. Identify which skill you're evaluating (mentioned in the conversation)
2. Use get_question tool to get a question (start with 'medium' difficulty)
3. Ask the question VERBATIM - do not modify it
4. Wait for the user's answer
5. Use check_answer tool to evaluate the answer
6. Decide next difficulty:
   - Correct answer → higher difficulty (max: hard)
   - Incorrect answer → lower difficulty (min: easy)
7. Repeat steps 2-6 until 3 questions asked
8. After 3 questions, hand off to "Interview Orchestrator Agent" with the evaluation result

# DECISION RULES:

- Do NOT give feedback on answers
- Ask exactly 3 questions per skill
- Pass if 2+ questions correct, otherwise fail

# HANDOFF FORMAT:

When handing off, include: "Evaluation complete. Result: [true/false]"
"""

# ==============================================================================
# AGENTS
# ==============================================================================

# Lab 14: Skill Extractor Agent
skill_extractor_agent = Agent(
    name="Skill Extractor Agent",
    instructions="""
You are an expert at analyzing job descriptions.

Extract the required technical skills from the given job description.
Include:
- Programming languages (Python, Java, etc.)
- Frameworks (LangChain, React, FastAPI, etc.)
- Cloud/Infrastructure (AWS, Docker, Kubernetes, etc.)
- Databases (SQL, PostgreSQL, MongoDB, etc.)
- Other technical skills mentioned

Return only concrete skill names as a list.
""",
    model="gpt-4.1",
    output_type=ExtractedSkills
)

# ==============================================================================
# TOOLS - Lab 14
# ==============================================================================

@function_tool
def extract_skills(session_id: str, job_id: int) -> list[str]:
    """Given a job_id, lookup job description from database and extract skills using AI"""
    job_id = int(job_id)
    
    # 1. Fetch JobPost from real database
    db_session = get_db_session()
    try:
        job_post = db_session.query(JobPost).filter(JobPost.id == job_id).first()
        if not job_post:
            raise ValueError(f"JobPost with id {job_id} not found")
        job_description = job_post.description
        print(f"Fetched JobPost #{job_id}: {job_post.title}")
    finally:
        db_session.close()
    
    # 2. Extract skills using LangChain
    llm = ChatOpenAI(model="gpt-4.1", temperature=0, api_key=settings.OPENAI_API_KEY)
    parser = PydanticOutputParser(pydantic_object=ExtractedSkills)
    
    prompt = PromptTemplate.from_template("""
Extract technical skills from this job description.

Return a JSON with a "skills" field containing a list of skill names.
Focus on: programming languages, frameworks, databases, cloud platforms.

{format_instructions}

Job Description:
{description}
""").partial(format_instructions=parser.get_format_instructions())
    
    chain = prompt | llm | parser
    result = chain.invoke({"description": job_description})
    extracted_skills = result.skills
    
    # 3. Filter to only skills that exist in question_bank
    available_skills = list(question_bank.keys())  # ["python", "sql", "system design"]
    skills = []
    for skill in extracted_skills:
        skill_lower = skill.lower()
        for available in available_skills:
            if available in skill_lower or skill_lower in available:
                # Capitalize properly
                skills.append(available.title() if available != "system design" else "System Design")
                break
    
    # Fallback: if no matching skills found, use defaults
    if not skills:
        skills = ["Python", "SQL", "System Design"]
        print(f"No matching skills found, using defaults: {skills}")
    
    # 4. Save to interview state
    if session_id not in interview_state:
        interview_state[session_id] = {"skills": [], "evaluation": []}
    interview_state[session_id]["skills"] = skills
    
    print(f"Extracted skills (filtered): {skills}")
    return skills


@function_tool
def update_evaluation(session_id: str, skill: str, evaluation_result: bool) -> bool:
    """Save evaluation result to the database"""
    try:
        print(f"Saving to DB: {skill} - {evaluation_result}")
        if isinstance(evaluation_result, str):
            evaluation_result = evaluation_result.lower() == "true"
        
        if session_id not in interview_state:
            interview_state[session_id] = {"skills": [], "evaluation": []}
        interview_state[session_id]["evaluation"].append((skill, evaluation_result))
        return True
    except KeyError:
        return False


# ==============================================================================
# TOOLS - Lab 15
# ==============================================================================

@function_tool
def get_question(topic: str, difficulty: Literal['easy', 'medium', 'hard']) -> str:
    """Return a question from the question bank given a topic and the difficulty of the question"""
    try:
        questions = question_bank[topic.lower()][difficulty.lower()]
        question = random.choice(questions)
        print(f"📝 Question ({difficulty}): {question}")
        return question
    except KeyError:
        return f"No questions available for topic '{topic}' at difficulty '{difficulty}'"


@function_tool
def check_answer(skill: str, question: str, answer: str) -> str:
    """Given a question and an answer for a particular skill, validate if the answer is correct"""
    
    # LangChain components
    llm = ChatOpenAI(model="gpt-4.1", temperature=0, api_key=settings.OPENAI_API_KEY)
    parser = PydanticOutputParser(pydantic_object=ValidationResult)
    prompt = PromptTemplate.from_template(VALIDATION_PROMPT).partial(
        format_instructions=parser.get_format_instructions()
    )
    
    # Create and invoke chain
    chain = prompt | llm | parser
    result = chain.invoke({"skill": skill, "question": question, "answer": answer})
    
    print(f"✅ Evaluation: {result.correct} - {result.reasoning}")
    return result.model_dump_json()


# ==============================================================================
# TOOLS - Lab 16
# ==============================================================================

@function_tool
def get_next_skill_to_evaluate(session_id: str) -> Optional[str]:
    """Retrieve the next skill to evaluate. Returns None if there are no more skills to evaluate"""
    if session_id not in interview_state:
        return None
    
    all_skills = interview_state[session_id]["skills"]
    evaluated = interview_state[session_id]["evaluation"]
    evaluated_skills = [item[0] for item in evaluated]
    remaining_skills = set(all_skills) - set(evaluated_skills)
    
    try:
        next_skill = remaining_skills.pop()
        print(f"NEXT SKILL: {next_skill}")
        return next_skill
    except KeyError:
        print("No more skills")
        return None


# ==============================================================================
# MAIN RUN FUNCTION (Lab 16)
# ==============================================================================

def run(session_id: str, job_id: int):
    """Run the multi-agent interview system with handoffs"""
    
    # 1. Create session
    session = SQLiteSession(f"screening-{session_id}")
    
    # 2. Create Orchestrator Agent
    orchestrator_agent = Agent(
        name="Interview Orchestrator Agent",
        instructions=ORCHESTRATOR_SYSTEM_PROMPT.format(
            RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX
        ),
        model="gpt-4.1",
        tools=[extract_skills, get_next_skill_to_evaluate, update_evaluation]
    )
    
    # 3. Create Evaluation Agent
    evaluation_agent = Agent(
        name="Skills Evaluator Agent",
        instructions=EVALUATION_SYSTEM_PROMPT.format(
            RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX
        ),
        model="gpt-4.1",
        tools=[get_question, check_answer]
    )
    
    # 4. Configure handoffs (bidirectional)
    orchestrator_agent.handoffs = [evaluation_agent]
    evaluation_agent.handoffs = [orchestrator_agent]
    
    # 5. Run the agent loop
    user_input = ORCHESTRATOR_USER_PROMPT.format(job_id=job_id, session_id=session_id)
    agent = orchestrator_agent
    
    while user_input != 'bye':
        result = Runner.run_sync(agent, user_input, session=session, max_turns=20)
        agent = result.last_agent
        print(result.final_output)
        user_input = input("User: ")


# ==============================================================================
# STANDALONE FUNCTIONS FOR TESTING
# ==============================================================================

def extract_skills_standalone(job_id: int) -> list[str]:
    """Standalone function to extract skills from a JobPost (for testing)"""
    db_session = get_db_session()
    try:
        job_post = db_session.query(JobPost).filter(JobPost.id == job_id).first()
        if not job_post:
            raise ValueError(f"JobPost with id {job_id} not found")
        job_description = job_post.description
    finally:
        db_session.close()
    
    result = Runner.run_sync(
        skill_extractor_agent,
        f"Extract skills from this job description:\n\n{job_description}"
    )
    
    return result.final_output.skills


def check_answer_standalone(skill: str, question: str, answer: str) -> ValidationResult:
    """Standalone function to validate an answer using LangChain (for testing)"""
    llm = ChatOpenAI(model="gpt-4.1", temperature=0, api_key=settings.OPENAI_API_KEY)
    parser = PydanticOutputParser(pydantic_object=ValidationResult)
    prompt = PromptTemplate.from_template(VALIDATION_PROMPT).partial(
        format_instructions=parser.get_format_instructions()
    )
    
    chain = prompt | llm | parser
    result = chain.invoke({"skill": skill, "question": question, "answer": answer})
    
    return result


def get_next_skill_standalone(session_id: str) -> Optional[str]:
    """Standalone function for testing get_next_skill_to_evaluate logic"""
    if session_id not in interview_state:
        return None
    
    all_skills = interview_state[session_id]["skills"]
    evaluated = interview_state[session_id]["evaluation"]
    evaluated_skills = [item[0] for item in evaluated]
    remaining_skills = set(all_skills) - set(evaluated_skills)
    
    try:
        return remaining_skills.pop()
    except KeyError:
        return None


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    """Main function - runs Lab 16 multi-agent interview system"""
    set_default_openai_key(settings.OPENAI_API_KEY)
    
    job_id = 1
    session_id = "session123"
    
    print("=" * 60)
    print("Multi-Agent Interview System (Lab 16 - Handoffs)")
    print("=" * 60)
    print("Type 'bye' to exit at any time")
    print("=" * 60)
    
    run(session_id, job_id)
    
    print("\n" + "=" * 60)
    print(f"FINAL EVALUATION STATE: {interview_state}")
    print("=" * 60)


if __name__ == "__main__":
    main()
