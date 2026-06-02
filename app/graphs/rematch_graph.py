from langgraph.graph import StateGraph


class MatchState(dict):
    pass


def check_score(state):

    if state["score"] < 0.65:

        state["retry"] = True

    else:

        state["retry"] = False

    return state


def reanalyze_resume(state):

    # LLM 재분석
    # semantic 강화

    enhanced = (
        state["resume_text"] +
        "\n추가 역량 분석"
    )

    state["enhanced_resume"] = enhanced

    return state


def final_matching(state):

    # 재 similarity 계산

    state["final_score"] = (
        state["score"] + 0.1
    )

    return state


builder = StateGraph(MatchState)

builder.add_node(
    "check_score",
    check_score
)

builder.add_node(
    "reanalyze_resume",
    reanalyze_resume
)

builder.add_node(
    "final_matching",
    final_matching
)

builder.set_entry_point(
    "check_score"
)

builder.add_edge(
    "check_score",
    "reanalyze_resume"
)

builder.add_edge(
    "reanalyze_resume",
    "final_matching"
)

graph = builder.compile()