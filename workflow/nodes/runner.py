# Nodes that save the generated test and run it with Playwright

import glob
import os
import subprocess

from workflow.state import TestState


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
