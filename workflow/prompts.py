# The prompts sent to the AI


def generate_prompt(test_case: str, page_snapshot: str):
    return f"""
You are a QA automation engineer.
Convert the manual test case below into a Playwright test in TypeScript.

Rules:
- Use Playwright Test: import {{ test, expect }} from '@playwright/test';
- Write one test() for the whole test case, using the `page` fixture.
- Use await expect() for every verification step.
- Use locators like getByRole() and getByPlaceholder() based on the page snapshot below.
- Only use elements that exist in the page snapshot. Do not guess the page title.
- If an element named in the test case does not exist in the page snapshot,
  do not replace it. Use the exact name from the test case so the test fails.
- Return ONLY TypeScript code. No explanation, no markdown.

Manual test case:
{test_case}

Page snapshot of the starting page (real elements on the page):
{page_snapshot}
"""


def fix_prompt(test_case: str, page_snapshot: str, test_code: str, error: str):
    return f"""
The Playwright test below failed. Fix it.
The error message contains a snapshot of the real page at the moment it failed.
Use it, and the starting page snapshot below, to correct locators and expected values.
Only use elements that exist in a snapshot. Do not guess.
If an element named in the test case does not exist in a snapshot,
do not replace it. Keep the exact name from the test case so the test keeps failing.
Return ONLY the full fixed TypeScript code. No explanation, no markdown.

Manual test case:
{test_case}

Page snapshot of the starting page (real elements on the page):
{page_snapshot}

Test code:
{test_code}

Error message:
{error}
"""
