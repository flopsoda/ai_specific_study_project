import os
os.environ["GRPC_VERBOSITY"] = "NONE" 
os.environ["GRPC_TRACE"] = ""
from typing import List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from agents import (
    GraphState, 
    main_writer_node,
    generate_character_opinion, 
    race_for_action,
    should_continue
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
        print("--- 라우팅: 토론 종료, 'main_writer_node' (으)로 이동 ---")
        return "main_writer_node"
    else:
        # 발언권을 얻은 캐릭터가 있으면 의견 생성 노드로 이동
        print(f"--- 라우팅: '{selected_character}'의 의견 생성 ---")
        return "generate_character_opinion"


# --- 그래프 구성 및 컴파일 ---
def build_graph():

    workflow = StateGraph(GraphState)

    # 1 노드 추가
    workflow.add_node("race_for_action", race_for_action) # 경쟁 노드 추가
    workflow.add_node("generate_character_opinion",generate_character_opinion) # 의견 생성 노드 추가
    workflow.add_node("main_writer_node", main_writer_node) # 메인 작가 노드 추가가
    workflow.add_node("should_continue_node", should_continue) # 계속할지 묻는 노드

    # 2. 진입점 설정
    workflow.set_entry_point("should_continue_node") 
    # 3. 엣지 연결 
    # 사용자가 계속하기를 원하면 토론 시작
    workflow.add_conditional_edges(
        "should_continue_node",
        lambda state: "race_for_action" if state.get("selected_character") == "start_discussion" else "end",
        {
            "race_for_action": "race_for_action",
            "end": END
        }
    )
    # 토론 진행 여부에 따라 분기
    workflow.add_conditional_edges(
        "race_for_action",
        route_discussion,
        {
            "generate_character_opinion": "generate_character_opinion",
            "main_writer_node": "main_writer_node"
        }
    )

    # 캐릭터가 의견을 생성하면 다시 토론 참여 경쟁으로 돌아감
    workflow.add_edge("generate_character_opinion", "race_for_action")
    
    # 작가가 글 작성을 마치면 다시 계속할지 물어봄
    workflow.add_edge("main_writer_node", "should_continue_node")

    # 4. 그래프 컴파일
    return workflow.compile()