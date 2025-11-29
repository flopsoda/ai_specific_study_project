import os
from typing import List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from agents import (
    GraphState, 
    main_writer_node,
    generate_character_opinion, 
    race_for_action,
    check_continuation,
    retrieve_memory_node,
    route_continuation,
    judge_node,     
    finalize_node    
)


# --- 토론 라우팅 함수 ---
def route_discussion(state: GraphState):
    """토론을 계속할지, 아니면 다음 단계로 넘길지 결정합니다."""
    selected_character = state.get("selected_character")
    phase = state.get("phase", "ideation")
    
    if selected_character == "None":
        print("--- 토론 끝 ---")
        if phase == "ideation":
            return "main_writer_node"
        else:
            return "judge_node"
    else:
        return "generate_character_opinion"


# --- 심사 라우팅 함수 ---
def route_judge(state: GraphState):
    """심사 결과에 따라 확정 또는 수정으로 분기합니다."""
    judge_result = state.get("judge_result")
    revision_count = state.get("revision_count", 0)
    
    # 무한 루프 방지: 3회 이상 수정했으면 강제 통과
    if revision_count >= 3:
        print("⚠️ [System] 수정 횟수 초과 → 강제 확정")
        return "finalize_node"
    
    if judge_result == "pass":
        return "finalize_node"
    else:
        return "main_writer_node"


# --- 그래프 구성 및 컴파일 ---
def build_graph():
    workflow = StateGraph(GraphState)

    # 1. 노드 추가
    workflow.add_node("check_continuation", check_continuation)
    workflow.add_node("retrieve_memory_node", retrieve_memory_node)
    workflow.add_node("race_for_action", race_for_action)
    workflow.add_node("generate_character_opinion", generate_character_opinion)
    workflow.add_node("main_writer_node", main_writer_node)
    workflow.add_node("judge_node", judge_node)
    workflow.add_node("finalize_node", finalize_node)

    # 2. 진입점
    workflow.set_entry_point("check_continuation")

    # 3. 엣지 연결
    
    # 사용자 확인 → 기억 검색
    workflow.add_conditional_edges(
        "check_continuation",
        route_continuation,
        {
            "race_for_action": "retrieve_memory_node",
            END: END
        }
    )

    # 기억 검색 → 발언권 경쟁
    workflow.add_edge("retrieve_memory_node", "race_for_action")

    # 발언권 경쟁 → (분기) → 의견 생성 OR 메인 작가 OR 심사
    workflow.add_conditional_edges(
        "race_for_action",
        route_discussion,
        {
            "main_writer_node": "main_writer_node",
            "generate_character_opinion": "generate_character_opinion",
            "judge_node": "judge_node"
        }
    )

    # 의견 생성 → 다시 경쟁
    workflow.add_edge("generate_character_opinion", "race_for_action")

    # 메인 작가 → 비평 회의 시작
    workflow.add_edge("main_writer_node", "race_for_action")

    # 심사 → (분기) → 확정 OR 다시 수정
    workflow.add_conditional_edges(
        "judge_node",
        route_judge,
        {
            "finalize_node": "finalize_node",
            "main_writer_node": "main_writer_node"
        }
    )

    # 확정 → 사용자 확인 (다음 문단 사이클)
    workflow.add_edge("finalize_node", "check_continuation")

    return workflow.compile()