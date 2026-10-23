# Human-in-the-loop nodes (ask before commit and push) and the git nodes

import subprocess
from langgraph.types import interrupt
from config import GIT_BRANCH
from workflow.state import TestState


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
