# Lab 22: LLM as a Judge

In this lab, we will create an LLM as a Judge scorer in braintrust.

This scorer will check if the revised job description is maintaining the correct structure

## High Level Overview

1. Go to the Scorers section of Braintrust

- Name: JD Structure Judge
- Type: LLM Judge

Give the prompt configuration as follows

System Prompt

```
You are a job description reviewer. You goal is to review the structure of the given job description and return whether it follows the correct structure or not.

The correct structure follows this format:

1. Job overview is mentioned in the first sentence
1. This is followed by the job responsibilities
1. Then we have the must have skills followed by nice to have skills
1. Finally the benefits of what the company offers are mentioned

After evaluating the job description structure, choose one of the following outputs:

- Bad: Less than three parts of the structure are followed
- Average: Three parts of the structure are followed
- Excellent: All four parts of the structure are followed
```

User Prompt

```
This is the job description to evaluate

{{output.revised_description}}
```

1. In the "Choice Scores" section, enter the following choices

- Bad (Score 0)
- Average (Score 50)
- Good (Score 100)

1. Set the Threshold slider to 49%
1. Use the Editor pane to test the judge with some inputs and iterate on the prompt until it is satisfactory
1. Save the scorer
