# All settings for the test generator in one place

import os

from dotenv import load_dotenv

# Load OPENAI_API_KEY (and optional OPENAI_MODEL) from the .env file
load_dotenv()

# AI model used to write and fix tests. Set OPENAI_MODEL in .env to change it.
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

# How many times to run the test (first try + fixes) before giving up
MAX_ATTEMPTS = 3

# Where the manual test cases are, and where generated tests are saved
TEST_CASES_DIR = "test_cases"

TESTS_DIR = "tests"

# Git branch to push to
GIT_BRANCH = "main"
