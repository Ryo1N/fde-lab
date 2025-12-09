"""
Lab 13: Using OpenAI Agents SDK

This module implements a simple interview screening agent using the OpenAI Agents SDK.
The SDK handles tool execution and conversation management automatically.

Changes from Lab 12:
- Removed manual JSON parsing and tool execution
- Added @function_tool decorators to tools
- Simplified prompts (removed JSON schema and tool definitions)
- Using Agent, Runner, and SQLiteSession from SDK
"""

from config import settings
from agents import Agent, Runner, function_tool, set_default_openai_key, SQLiteSession

# ==============================================================================
# DATABASE (Simulated with a dictionary)
# ==============================================================================

db = {
    "job_descriptions": {
        1: "I need an AI Engineer who knows langchain"
    },
    "state": {
        "session123": {
            "skills": [],
            "evaluation": []  # list of tuples (Skill, True/False), eg: [("Python", True)]
        }
    }
}

# ==============================================================================
# TOOLS (with @function_tool decorator)
# ==============================================================================

@function_tool
def extract_skills(session_id: str, job_id: int) -> list[str]:
    """Given a job_id, lookup job description and extract the skills for that job description"""
    job_id = int(job_id)
    job_description = db["job_descriptions"][job_id]
    skills = ["Python", "SQL", "System Design"]
    db["state"][session_id]["skills"] = skills
    print(f"Extracted skills: {skills}")
    return skills


@function_tool
def transfer_to_skill_evaluator(session_id: str, skill: str) -> bool:
    """This function takes a skill, evaluates it and returns the evaluation result for the skill as a boolean pass / fail"""
    result = True
    print(f"Evaluating skill: {skill}. Result {result}")
    return result


@function_tool
def update_evaluation(session_id: str, skill: str, evaluation_result: bool) -> bool:
    """This function takes the session_id, skill, and the evaluation result and saves it to the database. Returns success or failure (bool)"""
    try:
        print(f"Saving to DB: {skill} - {evaluation_result}")
        if isinstance(evaluation_result, str):
            evaluation_result = True if evaluation_result == "True" else False
        db["state"][session_id]["evaluation"].append((skill, evaluation_result))
        return True
    except KeyError:
        return False


# ==============================================================================
# PROMPTS (Simplified - no JSON schema or tool definitions needed)
# ==============================================================================

ORCHESTRATOR_SYSTEM_PROMPT = """
You are an interview orchestrator. Your goal is to evaluate the candidate on the required skills.

# INSTRUCTIONS

Follow the following steps exactly

1. Extract key skills from the job description using extract_skills tool
2. Then welcome the candidate, explain the screening process and ask the candidate if they are ready
3. Then, for EACH skill in the list, use transfer_to_skill_evaluator tool to delegate evaluation
4. Once you get the response, use the update_evaluation tool to save the evaluation result into the database
5. Once all skills are evaluated, mention that the screening is complete and thank the candidate for their time
"""

ORCHESTRATOR_USER_PROMPT = """
Start an interview for the following values:

session_id: {session_id}
job_id: {job_id}

Begin by welcoming the applicant, extracting the key skills, then evaluate each one.
"""

# ==============================================================================
# ORCHESTRATOR AGENT (Using SDK)
# ==============================================================================

def run_orchestrator_agent(session_id: str, job_id: int):
    """
    Run the orchestrator agent using OpenAI Agents SDK.
    
    The SDK handles:
    - Tool execution automatically
    - Conversation history management
    - JSON parsing and response handling
    """
    # Create session for conversation persistence
    session = SQLiteSession(f"screening-{session_id}")
    
    # Create the agent with tools
    agent = Agent(
        name="Interview Orchestrator Agent",
        instructions=ORCHESTRATOR_SYSTEM_PROMPT,
        model="gpt-4.1",
        tools=[extract_skills, transfer_to_skill_evaluator, update_evaluation]
    )
    
    # Format initial user input
    user_input = ORCHESTRATOR_USER_PROMPT.format(job_id=job_id, session_id=session_id)
    
    # Main loop - SDK handles tool calls automatically
    while user_input.lower() != "bye":
        result = Runner.run_sync(agent, user_input, session=session)
        print(f"\nAgent: {result.final_output}\n")
        user_input = input("User: ")


# ==============================================================================
# MAIN ENTRY POINT
# ==============================================================================

def main():
    """Main function to run the interview screening agent."""
    # Set OpenAI API key for the SDK
    set_default_openai_key(settings.OPENAI_API_KEY)
    
    job_id = 1
    session_id = "session123"
    
    print("=" * 60)
    print("Interview Screening Agent (OpenAI Agents SDK)")
    print("=" * 60)
    print("Type 'start' to begin the interview")
    print("Type 'bye' to exit at any time")
    print("=" * 60)
    
    run_orchestrator_agent(session_id, job_id)
    
    print("\n" + "=" * 60)
    print(f"FINAL EVALUATION STATUS: {db['state'][session_id]}")
    print("=" * 60)


if __name__ == "__main__":
    main()
