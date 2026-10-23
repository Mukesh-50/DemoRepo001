# Node: read the manual test case file

import re
from workflow.state import TestState

def read_test_case(state: TestState):
    print(f"Reading test case from {state['input_file']}")
    with open(state["input_file"], "r") as file:
        test_case = file.read()

    # Find the first URL written in the test case
    app_url = re.search(r"https?://[^\s\)\]]+", test_case).group()
    return {"test_case": test_case, "app_url": app_url}

