# The State: the data that moves between the nodes of the graph

from typing import TypedDict


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
    