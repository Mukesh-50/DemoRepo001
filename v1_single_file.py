# VERSION 1: the whole workflow in a single file
# (Version 2 is the same workflow split into a framework: see main.py and workflow/)
#
# Generates a Playwright test for every manual test case in test_cases/
# Run:  python v1_single_file.py
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
from typing import TypedDict

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command, interrupt
from playwright.sync_api import sync_playwright


# ---------------------------------------------------------------
# Step 1: Settings
# ---------------------------------------------------------------
# Load OPENAI_API_KEY (and optional OPENAI_MODEL) from the .env file
load_dotenv()

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_ATTEMPTS = 3
TEST_CASES_DIR = "test_cases"
TESTS_DIR = "tests"
GIT_BRANCH = "main"

llm = ChatOpenAI(model=OPENAI_MODEL, temperature=0)


# ---------------------------------------------------------------
# Step 2: State (the data that moves between the nodes)
# ---------------------------------------------------------------
class TestState(TypedDict):
    input_file: str      # manual test case, e.g. test_cases/TC001.txt
    output_file: str     # generated test, e.g. tests/tc001.spec.ts
    app_url: str         # URL found in the test case
    test_case: str       # text of the manual test case
    page_snapshot: str   # real elements on the starting page
    test_code: str       # generated Playwright code
    run_result: str      # output of the last test run
    passed: bool         # did the last run pass?
    attempts: int        # how many times the test has been run
    commit: bool         # was the test committed?
    push: bool           # was the commit pushed?


# ---------------------------------------------------------------
# Step 3: Nodes (each node is a normal Python function)
# ---------------------------------------------------------------
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
    for fence in ["```typescript", "```ts", "```"]:
        text = text.replace(fence, "")
    return text.strip()


def generate_test(state: TestState):
    print("Generating Playwright test using AI...")
    prompt = f"""
You are a QA automation engineer.
Convert the manual test case below into a Playwright test in TypeScript.

Rules:
- Use Playwright Test: import {{ test, expect }} from '@playwright/test';
- Write one test() for the whole test case, using the `page` fixture.
- Use await expect() for every verification step.
- Use locators like getByRole() and getByPlaceholder() based on the page snapshot below.
- Only use elements that exist in the page snapshot. Do not guess the page title.
- Return ONLY TypeScript code. No explanation, no markdown.

Manual test case:
{state['test_case']}

Page snapshot of the starting page (real elements on the page):
{state['page_snapshot']}
"""
    response = llm.invoke(prompt)
    return {"test_code": clean_code(response.content), "attempts": 1}


def save_test(state: TestState):
    print(f"Saving test to {state['output_file']}")
    os.makedirs(os.path.dirname(state["output_file"]), exist_ok=True)
    with open(state["output_file"], "w") as file:
        file.write(state["test_code"])
    return {}


def run_test(state: TestState):
    print(f"Running the generated test (attempt {state['attempts']})...")
    result = subprocess.run(
        # --headed opens a visible browser window so you can watch the test run
        ["npx", "playwright", "test", state["output_file"], "--headed", "--reporter=list"],
        capture_output=True,
        text=True,
    )
    passed = result.returncode == 0
    print("Test PASSED" if passed else "Test FAILED")

    run_result = result.stdout + result.stderr
    # On failure, Playwright saves a snapshot of the page in error-context.md. Give it to the AI too.
    for context_file in glob.glob("test-results/**/error-context.md", recursive=True):
        with open(context_file) as file:
            run_result += "\n\nPage at the moment of failure:\n" + file.read()

    return {"run_result": run_result, "passed": passed}


def fix_test(state: TestState):
    print("Asking AI to fix the test using the error message...")
    prompt = f"""
The Playwright test below failed. Fix it.
The error message contains a snapshot of the real page at the moment it failed.
Use it, and the starting page snapshot below, to correct locators and expected values.
Only use elements that exist in a snapshot. Do not guess.
Return ONLY the full fixed TypeScript code. No explanation, no markdown.

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
    # Note: when the graph resumes, this node runs again from the top.
    # So we don't print() here; everything to show goes inside the interrupt message.
    message = ""
    if not state["passed"]:
        message += state["run_result"] + "\n"

    status = "PASSED" if state["passed"] else "FAILED"
    message += f"Test {status}. Do you want to commit {state['output_file']}? (yes/no): "

    # interrupt() pauses the graph here and waits for your answer
    answer = interrupt(message)
    return {"commit": answer.strip().lower() in ("yes", "y")}


def commit_test(state: TestState):
    print(f"Committing {state['input_file']} and {state['output_file']} to git")
    subprocess.run(["git", "add", state["input_file"], state["output_file"]])
    result = subprocess.run(
        # Listing the files after "--" commits only these two, even if other changes are staged
        ["git", "commit", "-m", f"Add Playwright test for {state['input_file']}", "--", state["input_file"], state["output_file"]],
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
    answer = interrupt(f"Do you want to push this commit to the {GIT_BRANCH} branch? (yes/no): ")
    return {"push": answer.strip().lower() in ("yes", "y")}


def push_test(state: TestState):
    print(f"Pushing to {GIT_BRANCH} branch...")
    result = subprocess.run(["git", "push", "origin", GIT_BRANCH], capture_output=True, text=True)
    if result.returncode == 0:
        print("Push successful")
    else:
        print("Push failed:\n" + result.stderr)
    return {"push": result.returncode == 0}


# ---------------------------------------------------------------
# Step 4: Decision functions (pick the next step for conditional edges)
# ---------------------------------------------------------------
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


# ---------------------------------------------------------------
# Step 5: Build the Graph
# ---------------------------------------------------------------
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

# A checkpointer is needed so the graph can pause (interrupt) and resume later
app = graph.compile(checkpointer=MemorySaver())


# ---------------------------------------------------------------
# Step 6: Run the workflow once for every test case file
# ---------------------------------------------------------------
# Print the graph as an ASCII diagram (needs: pip install grandalf)
app.get_graph().print_ascii()

results = {}

for input_file in sorted(glob.glob(f"{TEST_CASES_DIR}/TC*.txt")):
    print(f"\n########## {input_file} ##########")
    # test_cases/TC001.txt -> tests/tc001.spec.ts
    name = os.path.basename(input_file).replace(".txt", "").lower()
    output_file = f"{TESTS_DIR}/{name}.spec.ts"

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
