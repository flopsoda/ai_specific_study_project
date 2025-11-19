import os
from typing import List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from agents import (
    GraphState, 
    main_writer_node,
    generate_character_opinion, 
    race_for_action,
    check_continuation, # 추가
    route_continuation  # 추가
)
from config import CHARACTERS
# --- 토론 라우팅 함수 ---
def route_discussion(state: GraphState):
    """
    토론을 계속할지, 아니면 작가에게 넘길지 결정합니다.
    """
    selected_character = state.get("selected_character")
    
    if selected_character == "None":
        # 토론에 참여할 캐릭터가 더 이상 없으면 작가 노드로 이동
        print("---토론 끝---")
        #print("--- 라우팅: 토론 종료, 'main_writer_node' (으)로 이동 ---")
        return "main_writer_node"
    else:
        # 발언권을 얻은 캐릭터가 있으면 의견 생성 노드로 이동
       # print(f"--- 라우팅: '{selected_character}'의 의견 생성 ---")
        return "generate_character_opinion"


# --- 그래프 구성 및 컴파일 ---
def build_graph():
    workflow = StateGraph(GraphState)

    # 1. 노드 추가
    workflow.add_node("race_for_action", race_for_action)
    workflow.add_node("generate_character_opinion", generate_character_opinion)
    workflow.add_node("main_writer_node", main_writer_node)
    workflow.add_node("check_continuation", check_continuation) # 대기 노드 추가

    # 2. 진입점
    workflow.set_entry_point("race_for_action")

    # 3. 엣지 연결
    
    # 토론 라우팅 (기존과 동일)
    workflow.add_conditional_edges(
        "race_for_action",
        route_discussion,
        {
            "generate_character_opinion": "generate_character_opinion",
            "main_writer_node": "main_writer_node"
        }
    )

    # 캐릭터 의견 생성 후 -> 다시 경쟁 (기존과 동일)
    workflow.add_edge("generate_character_opinion", "race_for_action")

    # [변경] 작가가 글을 쓰면 -> 바로 끝나는 게 아니라 -> 사용자 확인 노드로 이동
    workflow.add_edge("main_writer_node", "check_continuation")

    # [추가] 사용자 확인 노드에서 -> 계속할지 끝낼지 분기
    workflow.add_conditional_edges(
        "check_continuation",
        route_continuation,
        {
            "race_for_action": "race_for_action", # 계속하기
            END: END                              # 종료
        }
    )

    return workflow.compile()