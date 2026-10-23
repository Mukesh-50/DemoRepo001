# Start here: generates a Playwright test for every manual test case in test_cases/
#
# Run:  python main.py

import glob
import os
from langgraph.types import Command
from config import TEST_CASES_DIR, TESTS_DIR
from workflow.graph import app


def output_file_for(input_file: str):
    # test_cases/TC001.txt -> tests/tc001.spec.ts
    name = os.path.basename(input_file).replace(".txt", "").lower()
    return f"{TESTS_DIR}/{name}.spec.ts"


def run_workflow(input_file: str):
    # Each file gets its own thread_id so its pause/resume is tracked separately
    config = {"configurable": {"thread_id": input_file}}

    output = app.invoke({
        "input_file": input_file,
        "output_file": output_file_for(input_file),
    }, config)

    # The graph can pause more than once (commit? then push?).
    # Each time it pauses, ask the question and resume with the answer.
    while "__interrupt__" in output:
        question = output["__interrupt__"][0].value
        answer = input(question)
        output = app.invoke(Command(resume=answer), config)

    return output


def print_summary(results: dict):
    print("\n===== Summary =====")
    for input_file, output in results.items():
        # Was this test skipped?
        # If the test file already existed, the graph ended right at START,
        # so run_test never ran and "passed" was never added to the output.
        if "passed" in output:
            test_was_skipped = False
        else:
            test_was_skipped = True

        if test_was_skipped:
            print(f"{input_file} -> {output['output_file']}: SKIPPED (test already exists)")
        else:
            status = "PASSED" if output["passed"] else "FAILED"
            committed = "committed" if output["commit"] else "not committed"
            pushed = "pushed" if output.get("push") else "not pushed"
            print(f"{input_file} -> {output['output_file']}: {status} (attempts: {output['attempts']}, {committed}, {pushed})")


# Print the graph as an ASCII diagram (needs: pip install grandalf)
app.get_graph().print_ascii()

results = {}
for input_file in sorted(glob.glob(f"{TEST_CASES_DIR}/TC*.txt")):
    print(f"\n########## {input_file} ##########")
    results[input_file] = run_workflow(input_file)

print_summary(results)
