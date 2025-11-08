from typing import List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from agents import GraphState, call_main_agent, call_hamlet_agent, call_ophelia_agent, race_for_action,should_continue

# --- 캐릭터 선택 엣지 함수 ---
def route_to_character(state: GraphState):
    """
    선택된 캐릭터에 따라 다음 노드를 결정합니다.
    """
    selected_character = state.get("selected_character")
    print(f"--- 라우팅: '{selected_character}' (으)로 이동 ---")
    
    if selected_character == "hamlet":
        return "hamlet_agent"
    elif selected_character == "ophelia":
        return "ophelia_agent"
    else: # "None" 또는 예기치 않은 값일 경우
        # 아무도 행동하지 않으므로, 계속할지 여부를 바로 묻습니다.
        return "should_continue_node"


# --- 그래프 구성 및 컴파일 ---
def build_graph():

    workflow = StateGraph(GraphState)

    # 1. 노드 추가
    workflow.add_node("main_agent", call_main_agent)
    workflow.add_node("race_for_action", race_for_action) # 경쟁 노드 추가
    workflow.add_node("hamlet_agent", call_hamlet_agent) # 햄릿
    workflow.add_node("ophelia_agent", call_ophelia_agent) # 오필리아
    workflow.add_node("should_continue_node", should_continue) # 계속할지 묻는 노드

    # 2. 진입점 설정
    workflow.set_entry_point("main_agent") 
    # 3. 엣지 연결 
    workflow.add_edge("main_agent", "race_for_action") # 계속..?

    # 캐릭터 선택 후 라우팅
    workflow.add_conditional_edges(
        "race_for_action",
        route_to_character,
        {
            "hamlet_agent": "hamlet_agent",
            "ophelia_agent": "ophelia_agent",
            "should_continue_node": "should_continue_node" # 아무도 선택되지 않았을 때
        }
    )
    # 각 캐릭터 에이전트 실행 후 계속 여부 확인
    workflow.add_edge("hamlet_agent", "should_continue_node")
    workflow.add_edge("ophelia_agent", "should_continue_node")

    # 'should_continue_node' 실행 후, 업데이트된 상태를 보고 분기합니다.
    workflow.add_conditional_edges(
        "should_continue_node",
        # should_continue 노드가 업데이트한 'selected_character' 필드를 확인합니다.
        lambda state: state["selected_character"],
        {
            "main_agent": "main_agent",
            "end": END
        }
    )

    # 4. 그래프 컴파일
    return workflow.compile()