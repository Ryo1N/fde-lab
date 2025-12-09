# Lab 13: Open AI Agents SDK

In this lab, we will convert our previous code to use Open AI SDK interface.

First, update `requirements.txt` and install the dependency

```
openai-agents==0.6.2
```

## High Level Overview

1. At the beginning the OpenAI API key using `set_default_openai_key`
1. Apply the `@function_tool` decorator on the three tool functions
1. Remove the tools and output configurations from the system prompt
1. Now we need to update the `run_orchestrator_agent` function
1. Create a `SQLiteSession` with the name `screening-{session_id}`
1. Create the `Agent` class with model `gpt-5.1` and name `Interview Orchestrator Agent`
1. Fill in the job id and session id into the user prompt and set it as the initial user input
1. Call `Runner.run_sync` passing in the agent and session along with the user input
1. Print the response
1. Get the next user input
1. Repeat steps 8-10 until the user enters `bye`

## Hints

### How do I add the function_tool decorator?

<details>
<summary>Answer</summary>

First import

```python
from agents import function_tool
```

Then repeat this for all three tools

```
@function_tool
def extract_skills(session_id: str, job_id: int) -> list[str]:
    ...
```

</details>

### How do I configure the OPENAI_API_KEY

<details>
<summary>Answer</summary>

Import the required function

```python
from agents import set_default_openai_key
```

Then set it in `main` function

```python
def main():
    set_default_openai_key(settings.OPENAI_API_KEY)
    ...
```

</details>

### How do I set up the agent session?

<details>
<summary>Answer</summary>

```python
    session = SQLiteSession(f"screening-{session_id}")
```

</details>

### What change do I do to the system prompt?

<details>
<summary>Answer</summary>

Remove the Tools and Output configuration instructions so that it looks like this

```python
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
```

</details>

### How do I create the Agent?

<details>
<summary>Answer</summary>

```python
    agent = Agent(
        name="Interview Orchestrator Agent",
        instructions=ORCHESTRATOR_SYSTEM_PROMPT,
        model="gpt-5.1",
        tools=[extract_skills, transfer_to_skill_evaluator, update_evaluation]
    )
```

</details>

### How do I fill in job_id and session_id into the user prompt?

<details>
<summary>Answer</summary>

```python
    user_input = ORCHESTRATOR_USER_PROMPT.format(job_id=job_id, session_id=session_id)
```

</details>

### How do I run the agent?

<details>
<summary>Answer</summary>

```python
        result = Runner.run_sync(agent, user_input, session=session)
```

</details>

### How do I do keep running till the user inputs bye

<details>
<summary>Answer</summary>

```python
    while user_input != 'bye':
        result = Runner.run_sync(agent, user_input, session=session)
        print(result.final_output)
        user_input = input("User: ")
```

</details>
