# Lab 12: Building an agent by hand

Our goal is to build an agent for initial screening of applicants for a job. We will have a link which will open a chat session with the applicant. The agent will analyse the job description, decide which skills are needed and ask questions to the applicant on the relevant skills. It will then return the evaluation result that we can use to decide whom to call for the next round.

In this lab, we will build an agent by hand (without using any framework). This will help us understand how agents work internally. We need to know this when debugging agent workflows. In the next lab, we will update the code to use Open AI Agents SDK. And in third lab, we will build the full screening agent. Finally, in the fourth lab we will integrate with the rest of our application.

For this lab, we will build an agent with the following tools:

- Tool to extract skills given a job id
- Tool to evaluate competency in a given skill
- Tool to update the evaluation of a skill in the database

For this first lab, we will use a simplified implementation:

- Database will just be a dictionary object

```python
db = {
    "job_descriptions": {
        1: "I need an AI Engineer who knows langchain"
    },
    "state": {
        "session123": {
            "skills": [],
            "evaluation": [] # list of typles (Skill, True/False), eg: [("Python", True)]
        }
    }
}
```

- Skills will be hard coded to the following skills: `["Python", "SQL", "System Design"]`
- Evaluating competency will be hard coded to always return `True`
- Update skill to database should update to the above dictionary

## High Level Overview

1. Create the dummy database as shown above
1. Implement tool `def extract_skills(session_id: str, job_id: int) -> list[str]:`. It should return `["Python", "SQL", "System Design"]`. Also update it in the `db` dictionary.
1. Implement tool `def update_evaluation(session_id: str, skill: str, evaluation_result: bool) -> bool:`. Create a type and update the `evaluation` field in the `db` dictionary.
1. Implement tool `def transfer_to_skill_evaluator(session_id: str, skill: str) -> bool:`. Hardcoded to return `True`
1. Create a tool name to tool mapping: 

```python
tools_mapping = {
    "extract_skills": extract_skills,
    "update_evaluation": update_evaluation,
    "transfer_to_skill_evaluator": transfer_to_skill_evaluator
}
```

1. Use the below prompts

````python
ORCHESTRATOR_SYSTEM_PROMPT = """
You are an interview orchestrator. Your goal is to evaluate the candidate on the required skills.

# INSTRUCTIONS

Follow the following steps exactly

1. Extract key skills from the job description using extract_skills tool
2. Then welcome the candidate, explain the screening process and ask the candidate if they are ready 
3. Then, for EACH skill in the list, use transfer_to_skill_evaluator tool to delegate evaluation
4. Once you get the response, use the update_evaluation tool to save the evaluation result into the database
5. Once all skills are evaluated, mention that the screening is complete and thank the candidate for their time

# OUTPUT FORMAT

Output as a JSON following the JSON schema below:

```
{{
    "type": "object",
    "properties": {{
        "response": {{ "type": "string" }}
        "tool_name": {{ "type": "string"}},
        "tool_params": {{
            "type": "array",
            "items": {{
                "type": "object",
                "properties": {{
                    "param": {{ "type": "string" }},
                    "value": {{ "type": "string" }}
                }}
            }}
        }}
    }},
    "required": []
}}

Use the "tool_name" and "tool_params" properties to execute a tool and use the "response" property to reply to the user without a tool call. 

# TOOLS

You have access to the following tools

1. `extract_skills(session_id: str, job_id: int) -> list[str]`

Given a job_id, lookup job descriptiona and extract the skills for that job description

2. `update_evaluation(session_id: str, skill: str, evaluation_result: bool) -> bool`

This function takes the session_id, skill, and the evaluation result and saves it to the database. Returns success or failure (bool)

3. `transfer_to_skill_evaluator(session_id, skill: str) -> bool`

This function takes a skill, evaluates it and returns the evaluation result for the skill as a boolean pass / fail
"""

ORCHESTRATOR_USER_PROMPT = """
Start an interview for the following values:

session_id: {session_id}
job_id: {job_id}

Begin by welcoming the applicant, extracting the key skills, then evaluate each one.
"""
````

1. Now implement the `def run_orchestrator_agent(session_id, job_id):` function. 
1. We should first create the llm component using langchain
1. Create the messages list (initially only system message and user prompt)
1. Convert message list to prompt list using `ChatPromptTemplate`
1. Create a chain
1. Invoke the chain with the `job_id` and `session_id` as input
1. Once you get the response from the LLM, do the following
  - Append the response content to the messages list with type "assistant"
  - If the "response" field has a value, print it
  - If the "tool_name" field has a value,
    - Look up the name in the `tools_mapping` dict to get the corresponding python function
    - Get the parameters from the "tools_params" field
    - Call the python tool function with the appropriate parameters
    - Append the output of the tool to the messages list with type "ai"
  - If the "tool_name" is missing or empty, then get the input from the user
    - Append the user's input to the message list with the type "human"
  - Go back to step 4. Keep looping until the user types "bye"

Finally, implement a command line interface

```python
def main():
    job_id = 1
    session_id = "session123"
    run_orchestrator_agent(session_id, job_id)
    print(f"FINAL EVALUATION STATUS: {db['state'][session_id]}")

if __name__ == "__main__":
    main()
```

 Run this code from the command line:

 ```
 > python agents.py
 ```

 Type "start" to start and "bye" to quit.

## Hints

### How do I implement the extract_skills tool?

<details>
<summary>Answer</summary>
 
```python
def extract_skills(session_id: str, job_id: int) -> list[str]:
    """Given a job_id, lookup job descriptiona and extract the skills for that job description"""
    job_id = int(job_id)
    job_description = db["job_descriptions"][job_id]
    skills = ["Python", "SQL", "System Design"]
    db["state"][session_id]["skills"] = skills
    print(f"Extracted skills: {skills}")
    return skills
```
</details>

### How do I implement the transfer_to_skill_evaluator tool?

<details>
<summary>Answer</summary>
 
```python
def transfer_to_skill_evaluator(session_id: str, skill: str) -> bool:
    """This function takes a skill, evaluates it and returns the evaluation result for the skill as a boolean pass / fail"""
    result = True
    print(f"Evaluating skill: {skill}. Result {result}")
    return result
```
</details>

### How do I implement the update_evaluation tool?

<details>
<summary>Answer</summary>
 
```python
def update_evaluation(session_id: str, skill: str, evaluation_result: bool) -> bool:
    """This function takes the session_id, skill, and the evaluation result and saves it to the database. Returns success or failure (bool)"""
    try:
        print(f"Saving to DB: {skill} - {evaluation_result}")
        if isinstance(evaluation_result, str):
            evaluation_result = True if evaluation_result == "True" else False
        db["state"][session_id]["evaluation"]. append((skill, evaluation_result))
        return True
    except KeyError:
        return False
 ```
</details>

### How do I create the orchestration agent chain?

<details>
<summary>Answer</summary>
 
```python
def run_orchestrator_agent(session_id, job_id):
    llm = ChatOpenAI(model="gpt-5.1", temperature=0, api_key=settings.OPENAI_API_KEY)
    messages = [
        ("system", ORCHESTRATOR_SYSTEM_PROMPT),
        ("human", ORCHESTRATOR_USER_PROMPT),
    ]
    orchestrator_prompt = ChatPromptTemplate.from_messages(messages)
    orchestrator_chain = orchestrator_prompt | llm
    output = orchestrator_chain.invoke({"job_id": job_id, "session_id": session_id})
```
</details>

### How do I parse the LLM output?

<details>
<summary>Answer</summary>
 
```python
data = json.loads(output.content)
```
</details>

### How do I print the response field if it is present?

<details>
<summary>Answer</summary>
 
```python
if "response" in data:
    print(data["response"])
```
</details>

### How do I know if the response has a tool call or expects user input?

<details>
<summary>Answer</summary>

```python
if "tool_name" in data and data["tool_name"] != "":
    ... tool call logic ...
else:
    ... user input logic ...
```
</details>

### What do I do if there is a tool call?

<details>
<summary>Answer</summary>

```python
tool_name = data["tool_name"]
params = {param["param"]: param["value"] for param in data["tool_params"]}
tool_function = tools_mapping[tool_name]
tool_output = tool_function(**params)
print(f"TOOL OUTPUT = {tool_output}")
messages.append(("assistant", output.content.replace("{", "{{").replace("}", "}}")))
messages.append(("ai", str(tool_output)))
```
</details>

### What do I do user input is required?

<details>
<summary>Answer</summary>

```python
user_reply = input("User: ")
messages.append(("human", user_reply))
```
</details>

### How do I keep looping until the user says bye?

<details>
<summary>Answer</summary>

```python
user_reply = ""
while user_reply != "bye":
    ... all logic from step 4 onwards goes here ...
```
</details>