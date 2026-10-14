# Decision functions: each one picks the next step for a conditional edge

import os

from config import MAX_ATTEMPTS
from workflow.state import TestState


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
