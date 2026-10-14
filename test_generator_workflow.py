# LangGraph Workflow: Generate a Playwright test from every manual test case (TC*.txt)
#
# The workflow below runs once for each TC*.txt file in this folder.
#
# Flow:
#   START -> (test file already exists?) -> yes -> END (skip)
#                                        -> no  -> read_test_case -> read_page -> generate_test
#
#   generate_test -> save_test -> run_test -> (check result) -> passed -> ask_human
#                       ^                                    -> failed -> fix_test (max 3 tries)
#                       |                                                    |
#                       +----------------------------------------------------+
#
#   ask_human (pauses and asks you: commit?) -> yes -> commit_test -> ask_push
#                                            -> no  -> END
#
#   ask_push (pauses and asks you: push?)    -> yes -> push_test -> END
#                                            -> no  -> END

import glob
import os
import re
import subprocess
import sys
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from playwright.sync_api import sync_playwright

# Load OPENAI_API_KEY from the .env file
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

MAX_ATTEMPTS = 3


# Step 1: Define the State
class TestState(TypedDict):
    input_file: str
    app_url: str
    output_file: str
    test_case: str
    page_snapshot: str
    test_code: str
    run_result: str
    passed: bool
    attempts: int
    commit: bool
    push: bool


# Step 2: Create Nodes
def read_test_case(state: TestState):
    print(f"Reading test case from {state['input_file']}")
    with open(state["input_file"], "r") as file:
        test_case = file.read()

    # Find the first URL written in the test case
    app_url = re.search(r"https?://[^\s\)\]]+", test_case).group()
    return {"test_case": test_case, "app_url": app_url}


def read_page(state: TestState):
    print(f"Opening {state['app_url']} to read the real page elements")
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(state["app_url"])
        snapshot = f"Page title: {page.title()}\n" + page.locator("body").aria_snapshot()
        browser.close()
    return {"page_snapshot": snapshot}


def clean_code(text: str):
    # Remove ``` markdown fences if the AI added them
    return text.replace("```python", "").replace("```", "").strip()


def generate_test(state: TestState):
    print("Generating Playwright test using AI...")
    prompt = f"""
You are a QA automation engineer.
Convert the manual test case below into a Playwright test in Python using pytest.

Rules:
- Use pytest-playwright with the `page` fixture (from playwright.sync_api import Page, expect).
- Write one test function for the whole test case.
- Use expect() for every verification step.
- Use locators like get_by_role() and get_by_placeholder() based on the page snapshot below.
- Only use elements that exist in the page snapshot. Do not guess the page title.
- Return ONLY Python code. No explanation, no markdown.

Manual test case:
{state['test_case']}

Page snapshot of the starting page (real elements on the page):
{state['page_snapshot']}
"""
    response = llm.invoke(prompt)
    return {"test_code": clean_code(response.content), "attempts": 1}


def save_test(state: TestState):
    print(f"Saving test to {state['output_file']}")
    with open(state["output_file"], "w") as file:
        file.write(state["test_code"])
    return {}


def run_test(state: TestState):
    print(f"Running the generated test (attempt {state['attempts']})...")
    result = subprocess.run(
        # --headed opens a visible browser window so you can watch the test run
        [sys.executable, "-m", "pytest", state["output_file"], "-v", "--headed"],
        capture_output=True,
        text=True,
    )
    passed = result.returncode == 0
    print("Test PASSED" if passed else "Test FAILED")
    return {"run_result": result.stdout + result.stderr, "passed": passed}


def fix_test(state: TestState):
    print("Asking AI to fix the test using the error message...")
    prompt = f"""
The Playwright test below failed. Fix it.
The error message contains an "Aria snapshot" of the real page at the moment it failed.
Use it, and the starting page snapshot below, to correct locators and expected values.
Only use elements that exist in a snapshot. Do not guess.
Return ONLY the full fixed Python code. No explanation, no markdown.

Manual test case:
{state['test_case']}

Page snapshot of the starting page (real elements on the page):
{state['page_snapshot']}

Test code:
{state['test_code']}

Error message:
{state['run_result']}
"""
    response = llm.invoke(prompt)
    return {"test_code": clean_code(response.content), "attempts": state["attempts"] + 1}


def ask_human(state: TestState):
    status = "PASSED" if state["passed"] else "FAILED"
    if not state["passed"]:
        print(state["run_result"])
    # interrupt() pauses the graph here and waits for your answer
    answer = interrupt(f"Test {status}. Do you want to commit {state['output_file']}? (yes/no): ")
    return {"commit": answer.strip().lower() in ("yes", "y")}


def commit_test(state: TestState):
    print(f"Committing {state['input_file']} and {state['output_file']} to git")
    subprocess.run(["git", "add", state["input_file"], state["output_file"]])
    result = subprocess.run(
        ["git", "commit", "-m", f"Add Playwright test for {state['input_file']}"],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("Commit successful")
    else:
        print("Commit failed (maybe nothing changed):\n" + result.stdout + result.stderr)
    return {"commit": result.returncode == 0}


def ask_push(state: TestState):
    # Second human-in-the-loop pause
    answer = interrupt("Do you want to push this commit to the main branch? (yes/no): ")
    return {"push": answer.strip().lower() in ("yes", "y")}


def push_test(state: TestState):
    print("Pushing to main branch...")
    result = subprocess.run(["git", "push", "origin", "main"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Push successful")
    else:
        print("Push failed:\n" + result.stderr)
    return {"push": result.returncode == 0}


# Step 3: Decision functions
def check_test_exists(state: TestState):
    if os.path.exists(state["output_file"]):
        print(f"{state['output_file']} already exists, skipping")
        return "skip"
    return "new"


def check_result(state: TestState):
    if state["passed"]:
        return "done"
    if state["attempts"] >= MAX_ATTEMPTS:
        print(f"Giving up after {MAX_ATTEMPTS} attempts")
        return "done"
    return "fix"


def check_commit(state: TestState):
    if state["commit"]:
        return "commit"
    print("Not committing")
    return "skip"


def check_push(state: TestState):
    if state["push"]:
        return "push"
    print("Not pushing")
    return "skip"


# Step 4: Build the Graph
graph = StateGraph(TestState)

graph.add_node("read_test_case", read_test_case)
graph.add_node("read_page", read_page)
graph.add_node("generate_test", generate_test)
graph.add_node("save_test", save_test)
graph.add_node("run_test", run_test)
graph.add_node("fix_test", fix_test)
graph.add_node("ask_human", ask_human)
graph.add_node("commit_test", commit_test)
graph.add_node("ask_push", ask_push)
graph.add_node("push_test", push_test)

graph.add_conditional_edges(START, check_test_exists, {"skip": END, "new": "read_test_case"})
graph.add_edge("read_test_case", "read_page")
graph.add_edge("read_page", "generate_test")
graph.add_edge("generate_test", "save_test")
graph.add_edge("save_test", "run_test")
graph.add_conditional_edges("run_test", check_result, {"fix": "fix_test", "done": "ask_human"})
graph.add_edge("fix_test", "save_test")
graph.add_conditional_edges("ask_human", check_commit, {"commit": "commit_test", "skip": END})
graph.add_edge("commit_test", "ask_push")
graph.add_conditional_edges("ask_push", check_push, {"push": "push_test", "skip": END})
graph.add_edge("push_test", END)

# Step 5: Compile the graph
# A checkpointer is needed so the graph can pause (interrupt) and resume later
app = graph.compile(checkpointer=MemorySaver())


# Step 6: Run the workflow once for every test case file
if __name__ == "__main__":
    results = {}

    for input_file in sorted(glob.glob("TC*.txt")):
        print(f"\n########## {input_file} ##########")
        output_file = f"test_{input_file.replace('.txt', '').lower()}.py"  # TC001.txt -> test_tc001.py

        # Each file gets its own thread_id so its pause/resume is tracked separately
        config = {"configurable": {"thread_id": input_file}}

        output = app.invoke({
            "input_file": input_file,
            "output_file": output_file,
        }, config)

        # The graph can pause more than once (commit? then push?).
        # Each time it pauses, ask the question and resume with the answer.
        while "__interrupt__" in output:
            question = output["__interrupt__"][0].value
            answer = input(question)
            output = app.invoke(Command(resume=answer), config)

        results[input_file] = output

    print("\n===== Summary =====")
    for input_file, output in results.items():
        if "passed" not in output:
            print(f"{input_file} -> {output['output_file']}: SKIPPED (test already exists)")
        else:
            status = "PASSED" if output["passed"] else "FAILED"
            committed = "committed" if output["commit"] else "not committed"
            pushed = "pushed" if output.get("push") else "not pushed"
            print(f"{input_file} -> {output['output_file']}: {status} (attempts: {output['attempts']}, {committed}, {pushed})")
