# Lab 21: Custom Tracing

In this lab, we will see how we can create traces for specific workflows. In this example, we will create a trace for the "Review Job Description" workflow.

## High Level Overview

1. First we have to integrate langchain with braintrust. Open `ai.py` and follow the steps in the documentation - https://www.braintrust.dev/docs/integrations/sdk-integrations/langchain
1. Now any time we invoke a chain, it will create a trace on braintrust
1. Start the app (`fastapi dev main.py`) and go to the new job page. Add a job title and description and click `Review`. This will cause three chains to be invoked. You can use the data below to test

```
We’re seeking a Forward Deployed Engineer. We want someone with 3+ years of software engineering experience with production systems. They should be rockstar programmers and problem solvers. They should have experience in a customer-facing technical role with a background in systems integration or professional services
```

1. Go to Braintrust UI and you should see all the three traces there

By default, every chain invokation is a separate trace. It would be better if the entire review job description flow would be a single trace. Let us configure that

1. Import the `traced` decorator from the `braintrust` package
1. Apply `@traced(name='Review Job Description')` decorator to the `review_application` function
1. Now go back to the new job page and review the job description again.
1. Go to the braintrust UI and this time you should see a single trace which contains all the three chain invokation as spans within it

## Hints

### How do I configure langchain with braintrust?

<details>
<summary>Answer</summary>

Update `requirements.txt` then `pip install`

```
braintrust-langchain==0.1.5
```

Then open `ai.py` and add this code

```python
from braintrust import init_logger, traced
from braintrust_langchain import BraintrustCallbackHandler, set_global_handler

init_logger(project="Prodapt", api_key=settings.BRAINTRUST_API_KEY)
set_global_handler(BraintrustCallbackHandler())
```

</details>

### How do I create a customised trace?

<details>
<summary>Answer</summary>

Put the `@traced` decorator on the function

```python
@traced(name="Review Job Description")
def review_application(job_description: str) -> ReviewedApplication:
```

</details>
