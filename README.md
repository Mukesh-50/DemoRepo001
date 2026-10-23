# AI Test Generator with LangGraph

Turn a manual test case (a `.txt` file) into an automated **Playwright** test, using AI and **LangGraph**.

The workflow:
1. Reads a manual test case from `test_cases/`
2. Opens the web page to see the real elements on it
3. Asks the AI to write a Playwright test in TypeScript
4. Runs the test. If it fails, the AI fixes it (up to 3 tries)
5. Asks **you** whether to commit the test, then whether to push it
6. GitHub Actions runs all the tests after the push

## What you will learn

| LangGraph concept | Where to see it |
|---|---|
| **State**: data passed between steps | `workflow/state.py` |
| **Nodes**: one job per function | `workflow/nodes/` |
| **Edges**: the order of steps | `workflow/graph.py` |
| **Conditional edges**: choosing the next step | `workflow/decisions.py` |
| **Loops**: the fix-and-retry loop | `fix_test` → `save_test` in `workflow/graph.py` |
| **Human-in-the-loop**: pause and ask you | `interrupt()` in `workflow/nodes/git_ops.py`, resume in `main.py` |

## Prerequisites

- Python 3.10 or newer
- Node.js 20 or newer
- Git
- An OpenAI API key

## Setup (one time)

```bash
# 1. Python packages
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium        # browser used to read the page

# 2. Node packages (to run the generated tests)
npm install
npx playwright install chromium

# 3. Your OpenAI key
cp .env.example .env               # then open .env and paste your key
```

## Two versions of the same workflow

Both versions do exactly the same thing and use the same `test_cases/` and `tests/` folders. Only the code structure is different.

| | Version 1: single file | Version 2: framework |
|---|---|---|
| Run | `python v1_single_file.py` | `python main.py` |
| Code | Everything in one file | Split into `main.py`, `config.py` and `workflow/` |
| Best for | Learning: read the whole flow top to bottom | Real projects: easy to find, change and test one part |

Start with Version 1 to understand the workflow, then open Version 2 to see how the same code is organised into a framework.

## Run

```bash
python v1_single_file.py    # Version 1
python main.py              # Version 2
```

You will see:
- The graph printed as an ASCII diagram
- For each test case: generate → run → (fix) → `Do you want to commit?` → `Do you want to push?`
- A summary at the end

A test case is **skipped** if its test file already exists in `tests/`.
To generate it again, delete the file (for example `tests/tc001.spec.ts`) and run again.

## Add your own test case

Create a new file in `test_cases/`, for example `test_cases/TC005.txt`. It must:
- Start with `TC` and end with `.txt`
- Contain the URL of the page to test (`https://...`)
- Describe the steps and the expected result

Then run `python main.py`. Only the new test case is generated.

## Run the generated tests yourself

```bash
npx playwright test              # run all tests
npx playwright test --ui         # watch and debug in UI mode
npx playwright show-report       # open the HTML report
```

## Project structure

```
main.py                  ← start here
config.py                ← settings (model, max attempts, folders, branch)
test_cases/              ← manual test cases (TC*.txt)
tests/                   ← generated Playwright tests (*.spec.ts)
workflow/
├── state.py             ← TestState: the data that flows through the graph
├── graph.py             ← nodes + edges
├── decisions.py         ← decision functions for conditional edges
├── prompts.py           ← prompts sent to the AI
└── nodes/
    ├── test_case.py     ← read_test_case
    ├── browser.py       ← read_page
    ├── ai.py            ← generate_test, fix_test
    ├── runner.py        ← save_test, run_test
    └── git_ops.py       ← ask_human, commit_test, ask_push, push_test
.github/workflows/main.yml  ← runs the tests on GitHub after every push
```

**Suggested reading order:** `state.py` → `nodes/test_case.py` → `decisions.py` → `graph.py` → `main.py` → `nodes/ai.py` → `nodes/git_ops.py`

## Tips

- AI output is different on every run. If a test keeps failing, try a stronger model: add `OPENAI_MODEL=gpt-4.1` to `.env`.
- Never commit your `.env` file. It is already in `.gitignore`.
