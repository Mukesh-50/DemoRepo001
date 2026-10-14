# All nodes of the graph, so graph.py can import them from one place

from workflow.nodes.ai import fix_test, generate_test
from workflow.nodes.browser import read_page
from workflow.nodes.git_ops import ask_human, ask_push, commit_test, push_test
from workflow.nodes.runner import run_test, save_test
from workflow.nodes.test_case import read_test_case
