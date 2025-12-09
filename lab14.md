# Lab 14: Extract Skills (Homework)

We are returning a hardcoded value in the `extract_skills` tool.

Update this tool function so that:

1. Create a prompt to extract the technical skills from a job description
1. We want the output as a list of skills. Create an appropriate pydantic output parser
1. Create a langchain chain to extract the skills
1. Update extract_skills to fetch the job description from the real database
1. Then invoke the chain with the real job description
1. Return the list of skills
