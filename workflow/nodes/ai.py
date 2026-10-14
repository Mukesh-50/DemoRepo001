# Nodes that use the AI: write the test, and fix it when it fails

from langchain_openai import ChatOpenAI

from config import OPENAI_MODEL
from workflow.prompts import fix_prompt, generate_prompt
from workflow.state import TestState

llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)


def clean_code(text: str):
    # Remove ``` markdown fences if the AI added them
    for fence in ["```typescript", "```ts", "```"]:
        text = text.replace(fence, "")
    return text.strip()


def generate_test(state: TestState):
    print("Generating Playwright test using AI...")
    prompt = generate_prompt(state["test_case"], state["page_snapshot"])
    response = llm.invoke(prompt)
    return {"test_code": clean_code(response.content), "attempts": 1}


def fix_test(state: TestState):
    print("Asking AI to fix the test using the error message...")
    prompt = fix_prompt(state["test_case"], state["page_snapshot"], state["test_code"], state["run_result"])
    response = llm.invoke(prompt)
    return {"test_code": clean_code(response.content), "attempts": state["attempts"] + 1}
