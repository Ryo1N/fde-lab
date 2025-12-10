# Lab 20: Prompt Evaluation

In this lab, we will evaluate the prompt that was created in Braintrust in the previous lab

## Part 1: Create a dataset and evaluate the prompt

1. First we need to configure `AI Providers` in Braintrust. This will enable it to run prompts on the LLM using our token. Go to `Profile Photo -> Settings -> AI Providers` and configure your Open AI API key here
1. The create a dataset. Upload the file `test/check_answer_evaluation_dataset.json` for the dataset

- Give a name `Check Answer Evaluation Dataset`
- Set `skill`, `question` and `answer` as input fields
- Set `correct` as output field

1. Open up the prompt you created in the previous lab. In the top right click `Evaluation In` button and select `Playground`
1. In the Dataset button, select the dataset you created above
1. Set the model to `GPT-5` in the dropdown above the prompt
1. Press the `Run` button on the top right to run the dataset against the prompt

Braintrust will use the AI Provider API Key to run the prompt with the given inputs and will show all the outputs. At this point, we can manually inspect the output. If we are not happy with the output, we can modify the prompt and run the dataset again. Keep repeating until we get a prompt that we like. At this point, we can save this as a new version of the prompt. Our code will automatically pick up this new prompt version when we run our agent.

## Part 2: Create a custom scorer

Let us set up an automated scoring eval. This eval will check if the `correct` field has been set as expected or not. It does not check the `reasoning` field.

1. Click `Scorers` in the sidebar
1. Create a new scorer

- Name: Check Answer Correctness Scorer
- Type: Python

Because correctness can be checked exactly by code, we don't need LLM as a Judge here. Regular python code can check if the field is right or wrong.

Here is the code for the scorer

```python
  if expected is None:
    return None
  return output["correct"] == expected
```

All it does it reads the "correct" field in the output and checks if it matches the expectation.

1. Now go back to the Playground that we created for the prompt in Part 1
1. Click on the `+ Scorer` button and select the scorer we created above
1. Run the prompt against the dataset

This time, apart from showing the output for each row, it will also show the score from the Scorer that we created
