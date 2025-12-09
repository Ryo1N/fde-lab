# Lab 15: Multi Agent Systems

In this lab, we will implement the skills evaluator. This agent will take a skill as input (example `Python`) and it will ask up to three questions selected from a question bank.

This are the questioning rules:

- Questions are divided into easy, medium and hard
- The agent starts with a medium question
- If any question is answered correctly, the next question is higher difficulty
- If the answer is wrong, then the next quesion is lower difficulty
- If the first two questions are both answered correctly then questioning stops there after 2 questions
- Otherwise maximum 3 questions are asked in total

At the end, the agent returns the evaluation `True` or `False`. It is True if the last question was medium / hard difficulty and answered correctly. Otherwise False.

Tools required are:

1. `get_question(topic: str, difficulty: Literal['easy', 'medium', 'hard']) -> str`
1. `check_answer(skill: str, question: str, answer: str) -> Tuple[bool, str]`

Use this question bank

```python
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
            "Explain this SQL: SELECT product_name FROM products WHERE cost < 500'"
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
```

## High Level Overview

1. Add the question bank variable to the `agent.py` file
1. Implement `get_question(topic: str, difficulty: Literal['easy', 'medium', 'hard']) -> str` tool

- It should look up the questions from the question bank
- Use `random.choice()` function from `random` module to randomly choose a question
- Don't forget the decorator

1. Implement `check_answer(skill: str, question: str, answer: str) -> Tuple[bool, str]` tool

- This tool will use an LLM prompt to evaluate the answer

Use the following prompt and return type

```python
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

class ValidationResult(BaseModel):
    correct: bool
    reasoning: str
```

- Then create the `llm`, `parser`, `prompt` (We need to use `PromptTemplate` instead of `ChatPromptTemplate`. Why?) and finally the `chain`
- Invoke the chain with the `skill`, `question` and `answer` as inputs
- return `output.modul_dump_json()`

1. Test out this tool with these test cases

- Result `False`:

```python
check_answer("System Design", "Mention ways to speed up retrieval from a vector database", "One can use quantised vectors to save space")

```

- Result `True`

```python
check_answer("System Design", "Give an overview of Cost - Accuracy - Latency tradeoffs in an AI system", """
- Accuracy can be improved by using a better model, performing more exhaustive retrieval or adding more steps to the process (like query decomposition).
- However, these come at the expense of increased cost and latency
- Cost and latency can be reduced by using smaller and faster models, at the expense of accuracy
- Caching can be another way to save on both cost and latency

Thus, there is always a tradeoff between the three.""")
```

1. Now it is time to implement `run_evaluation_agent(session_id, skill)`

Use this prompt

```python
EVALUATION_SYSTEM_PROMPT = """
You are a specialised skill evaluator. Your job is to evaluate the candidate's proficiency in a given skill

1. Identify which skill you're evaluating (it will be mentioned in the conversation)
2. Use the get_question tool to get a question to ask (start with 'medium' difficulty). Ask the question verbatim, DO NOT MODIFY it in any way
3. After each candidate answer, use check_answer tool to evaluate
4. Decide the next question:
   - If the check_answer tool returned correct, choose the next higher difficulty, without going above 'hard'
   - If the check_answer tool returned incorrect, choose the lower difficulty, without going below 'easy'
   - Stop after 3 questions MAXIMUM
5. If the correctly answered two of the three questions, then they pass, otherwise they fail

DECISION RULES:
- Maximum 3 questions per skill

OUTPUT:

After the evaluation is complete, return the pass/fail in a json object with the following properties
- result: true or false
"""

EVALUATION_USER_PROMPT = """
Evaluate the user on the following skill: {skill}
"""
```

1. Follow similar steps to Lab 14 to implement this agent

- Create session same way as before
- Agent name: "Skills Evaluator Agent"
- Keep asking the user for input until they input 'bye'

1. Update `main()` function:

```python
def main():
    set_default_openai_key(settings.OPENAI_API_KEY)
    job_id = 1
    session_id = "session123"
    run_evaluation_agent(session_id, "Python")
```

1. Test from the command line

## Hints

### How do I implement get_question tool?

<details>
<summary>Answer</summary>

```python
@function_tool
def get_question(topic: str, difficulty: Literal['easy', 'medium', 'hard']) -> str:
    """Return a question from the question bank given a topic and the difficulty of the question"""
    questions = question_bank[topic.lower()][difficulty.lower()]
    return random.choice(questions)
```

</details>

### How do I implement check_answer tool?

<details>
<summary>Answer</summary>

```python
@function_tool
def check_answer(skill:str, question: str, answer: str) -> Tuple[bool, str]:
    """Given a question and an answer for a particular skill, validate if the answer is correct. Returns a tuple (correct, reasoning)"""

    llm = ChatOpenAI(model="gpt-5.1", temperature=0, api_key=settings.OPENAI_API_KEY)
    parser = PydanticOutputParser(pydantic_object=ValidationResult)
    prompt = PromptTemplate.from_template(VALIDATION_PROMPT).partial(format_instructions=parser.get_format_instructions())
    chain = prompt | llm | parser
    result = chain.invoke({"skill": skill, "question": question, "answer": answer})
    return result.model_dump_json()
```

</details>

### How do I implement the evaluation agent?

<details>
<summary>Answer</summary>

```python
def run_evaluation_agent(session_id, skill):
    session = SQLiteSession(f"screening-{session_id}")
    agent = Agent(
        name="Skills Evaluator Agent",
        instructions=EVALUATION_SYSTEM_PROMPT,
        model="gpt-5.1",
        tools=[get_question, check_answer]
    )
    user_input = EVALUATION_USER_PROMPT.format(skill=skill)
    while user_input != 'bye':
        result = Runner.run_sync(agent, user_input, session=session)
        print(result.final_output)
        user_input = input("User: ")
```

</details>
