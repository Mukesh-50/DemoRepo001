# Build the graph: which nodes exist and how they are connected
#
# Flow:
#   START -> (test file already exists?) -> yes -> END (skip)
#                                        -> no  -> read_test_case -> read_page -> generate_test
#
#   generate_test -> save_test -> run_test -> (check result) -> passed -> ask_human
#                       ^                                    -> failed -> fix_test (max 3 tries)
#                       |                                                    |
#                       +----------------------------------------------------+
#
#   ask_human (pauses and asks you: commit?) -> yes -> commit_test -> ask_push
#                                            -> no  -> END
#
#   ask_push (pauses and asks you: push?)    -> yes -> push_test -> END
#                                            -> no  -> END

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END

from workflow.decisions import check_commit, check_push, check_result, check_test_exists
from workflow.nodes import (
    ask_human,
    ask_push,
    commit_test,
    fix_test,
    generate_test,
    push_test,
    read_page,
    read_test_case,
    run_test,
    save_test,
)
from workflow.state import TestState

graph = StateGraph(TestState)

# Nodes
graph.add_node("read_test_case", read_test_case)
graph.add_node("read_page", read_page)
graph.add_node("generate_test", generate_test)
graph.add_node("save_test", save_test)
graph.add_node("run_test", run_test)
graph.add_node("fix_test", fix_test)
graph.add_node("ask_human", ask_human)
graph.add_node("commit_test", commit_test)
graph.add_node("ask_push", ask_push)
graph.add_node("push_test", push_test)

# Edges
graph.add_conditional_edges(START, check_test_exists, {"skip": END, "new": "read_test_case"})
graph.add_edge("read_test_case", "read_page")
graph.add_edge("read_page", "generate_test")
graph.add_edge("generate_test", "save_test")
graph.add_edge("save_test", "run_test")
graph.add_conditional_edges("run_test", check_result, {"fix": "fix_test", "done": "ask_human"})
graph.add_edge("fix_test", "save_test")
graph.add_conditional_edges("ask_human", check_commit, {"commit": "commit_test", "skip": END})
graph.add_edge("commit_test", "ask_push")
graph.add_conditional_edges("ask_push", check_push, {"push": "push_test", "skip": END})
graph.add_edge("push_test", END)

# Compile the graph
# A checkpointer is needed so the graph can pause (interrupt) and resume later
app = graph.compile(checkpointer=MemorySaver())
