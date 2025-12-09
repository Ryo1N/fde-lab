# Lab 16: Handoffs

We have individually written two agents:

- Orchestrator agent
- Evaluation agent

We now want to integrate both together, so that

- Orchestrator agent extracts list of skills
- Gets the first skill
- Hands over to evaluation agent to evaluate the skill
- Evaluation agent asks three questions and hands back to orchestration agent with the result
- Orchestrator agent saves it to the database
- Repeat from step 3 until all skills are done

Here, orchestrator agent and evaluation agent have to coordinate back and forth between them to complete the task.

## High Level Overview

1. First, we need to delete some code that we don't need anymore

- Delete the tool `transfer_to_skill_evaluator`
- Delete the function `run_orchestrator_agent`
- Delete the function `run_evaluation_agent`

1. Now we need to implement a new tool `get_next_skill_to_evaluate(session_id: str) -> str | None`

- It should return the next skill to evaluate
- It calculates this by looking in the DB
  - Find all the skills to tests (`skills` field)
  - See which skills have already been evaluated (`evaluation` field)
  - Find a skill that is remaining to be evaluated and return it
  - Return `None` if no more skills remaining

1. Then import this `from agents.extensions.handoff_prompt import RECOMMENDED_PROMPT_PREFIX`

- This is a prompt text that Open AI recommends that you add to the top of the system prompt for multi agent system

So update both agent system prompts as follows

```python
ORCHESTRATOR_SYSTEM_PROMPT = """
{RECOMMENDED_PROMPT_PREFIX}

You are an interview orchestrator. Your goal is to evaluate the candidate on the required skills.

# INSTRUCTIONS

Follow the following steps exactly

1. Extract key skills from the job description using extract_skills tool
2. Then welcome the candidate, explain the screening process and ask the candidate if they are ready
3. Then, use the get_next_skill_to_evaluate tool to get the skill to evaluate
4. If the skill is not `None` then hand off to the "Skills Evaluator Agent" to perform the evaluation. Pass in the skill to evaluate
4. Once you get the response, use the update_evaluation tool to save the evaluation result into the database
5. Once get_next_skill_to_evaluate returns `None`, return a json with a single field `status` set to "done" to indicate completion
"""

EVALUATION_SYSTEM_PROMPT = """
{RECOMMENDED_PROMPT_PREFIX}

You are a specialised skill evaluator. Your job is to evaluate the candidate's proficiency in a given skill

1. Identify which skill you're evaluating (it will be mentioned in the conversation)
2. Use the get_question tool to get a question to ask (start with 'medium' difficulty). Ask the question verbatim, DO NOT MODIFY it in any way
3. After each candidate answer, use check_answer tool to evaluate
4. Decide the next question:
   - If the check_answer tool returned correct, choose the next higher difficulty, without going above 'hard'
   - If the check_answer tool returned incorrect, choose the lower difficulty, without going below 'easy'
   - Stop after 3 questions MAXIMUM
5. If the correctly answered two of the three questions, then they pass, otherwise they fail
6. After completion of 3 questions, hand off to the "Interview Orchestrator Agent" passing in the result of the evaluation

# DECISION RULES:

- Do not give feedback on the user's answer. Always proceed to the next question
- 3 questions per skill

# OUTPUT:

After the evaluation is complete, return the pass/fail in a json object with the following properties
- result: true or false
"""
```

1. Now we will create the main function `def run(session_id, job_id):`

- This function replaces `run_orchestrator_agent` and `run_evaluation_agent`
- Create the `session`
- Create the `orchestrator_agent` (remember to pass in the new tool and remove the deleted one)
- Create the `evaluation_agent`
- In both the above, remember to fill in the value for the `RECOMMENDED_PROMPT_PREFIX`
- Configure the handoffs and run the agents as shown below

```python
    orchestrator_agent.handoffs = [evaluation_agent]
    evaluation_agent.handoffs = [orchestrator_agent]
    user_input = ORCHESTRATOR_USER_PROMPT.format(job_id=job_id, session_id=session_id)
    agent = orchestrator_agent
    while user_input != 'bye':
        result = Runner.run_sync(agent, user_input, session=session, max_turns=20)
        agent = result.last_agent
        print(result.final_output)
        user_input = input("User: ")
```

Finally, update `main()`

```python
def main():
    set_default_openai_key(settings.OPENAI_API_KEY)
    job_id = 1
    session_id = "session123"
    run(session_id, job_id)
    print("FINAL EVALUATION STATE", db)
```

And run the code

## Hints

### How to implement get_next_skill_to_evaluate?

<details>
<summary>Answer</summary>

```python
@function_tool
def get_next_skill_to_evaluate(session_id: str) -> str | None:
    """Retrieve the next skill to evaluate. Returns None if there are no more skills to evaluate"""
    all_skills = db["state"][session_id]["skills"]
    evaluated = db["state"][session_id]["evaluation"]
    evaluated_skills = [item[0] for item in evaluated]
    remaining_skills = set(all_skills) - set(evaluated_skills)
    try:
        next_skill = remaining_skills.pop()
        print("NEXT SKILL TOOL", next_skill)
        return next_skill
    except KeyError:
        print("No more skills")
        return None
```

</details>

### How to implement the session?

<details>
<summary>Answer</summary>

See previous lab

</details>

### How to implement the orchestrator agent?

<details>
<summary>Answer</summary>

```python
    orchestrator_agent = Agent(
        name="Interview Orchestrator Agent",
        instructions=ORCHESTRATOR_SYSTEM_PROMPT.format(RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX),
        model="gpt-5.1",
        tools=[extract_skills, get_next_skill_to_evaluate, update_evaluation]
    )
```

</details>

### How to implement the evaluation agent?

<details>
<summary>Answer</summary>

```python
    evaluation_agent = Agent(
        name="Skills Evaluator Agent",
        instructions=EVALUATION_SYSTEM_PROMPT.format(RECOMMENDED_PROMPT_PREFIX=RECOMMENDED_PROMPT_PREFIX),
        model="gpt-5.1",
        tools=[get_question, check_answer]
    )
```

</details>
