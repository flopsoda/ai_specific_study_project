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
    retrieve_memory_node, # [추가]
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
    workflow.add_node("check_continuation", check_continuation)
    workflow.add_node("retrieve_memory_node", retrieve_memory_node) # [추가]
    workflow.add_node("race_for_action", race_for_action)
    workflow.add_node("generate_character_opinion", generate_character_opinion)
    workflow.add_node("main_writer_node", main_writer_node)

    # 2. 진입점
    workflow.set_entry_point("check_continuation")

    # 3. 엣지 연결
    
    # [1] 사용자 확인 -> (계속) -> 기억 검색
    workflow.add_conditional_edges(
        "check_continuation",
        route_continuation,
        {
            "race_for_action": "retrieve_memory_node", # 원래 race로 갈 것을 memory로 납치(Redirect)
            END: END
        }
    )

    # [2] 기억 검색 -> 발언권 경쟁
    workflow.add_edge("retrieve_memory_node", "race_for_action")

    # [3] 발언권 경쟁 -> (분기) -> 의견 생성 OR 메인 작가
    # [중요] 기존의 add_edge("race_for_action", ...)는 지우고 아래 코드를 써야 합니다.
    workflow.add_conditional_edges(
        "race_for_action",
        route_discussion, # 여기서 None인지 아닌지 판단
        {
            "main_writer_node": "main_writer_node",
            "generate_character_opinion": "generate_character_opinion"
        }
    )

    # [4] 의견 생성 -> 다시 경쟁
    workflow.add_edge("generate_character_opinion", "race_for_action")

    # [5] 메인 작가 -> 다시 사용자 확인
    workflow.add_edge("main_writer_node", "check_continuation")

    return workflow.compile()