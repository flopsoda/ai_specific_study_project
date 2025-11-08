from typing import List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from agents import GraphState, node_environment, character_agents, race_for_action,should_continue
from config import CHARACTERS
# --- 캐릭터 선택 엣지 함수 ---
def route_to_character(state: GraphState):
    """
    선택된 캐릭터에 따라 다음 노드를 결정합니다.
    """
    selected_character = state.get("selected_character")
    print(f"--- 라우팅: '{selected_character}' (으)로 이동 ---")
    
    if selected_character in CHARACTERS:
        return f"{selected_character}_agent"
    else: # "None" 또는 예기치 않은 값일 경우
        # 아무도 행동하지 않으므로, 계속할지 여부를 바로 묻습니다.
        return "should_continue_node"


# --- 그래프 구성 및 컴파일 ---
def build_graph():

    workflow = StateGraph(GraphState)

    # 1.1 노드 추가
    workflow.add_node("node_environment", node_environment)
    workflow.add_node("race_for_action", race_for_action) # 경쟁 노드 추가
    workflow.add_node("should_continue_node", should_continue) # 계속할지 묻는 노드

    # 1.2 캐릭터 에이전트 노드 추가
    for node_name, node_function in character_agents.items():
        workflow.add_node(node_name, node_function)

    # 2. 진입점 설정
    workflow.set_entry_point("node_environment") 
    # 3. 엣지 연결 
    workflow.add_edge("node_environment", "race_for_action") # 계속..?

    # 캐릭터 선택 후 라우팅 (동적으로 매핑 생성)
    character_routing_map = {
        f"{name}_agent": f"{name}_agent" for name in CHARACTERS.keys()
    }
    character_routing_map["should_continue_node"] = "should_continue_node"

    workflow.add_conditional_edges(
        "race_for_action",
        route_to_character,
        character_routing_map
    )

    # 각 캐릭터 에이전트 실행 후 계속 여부 확인
    for name in CHARACTERS.keys():
        workflow.add_edge(f"{name}_agent", "should_continue_node")

    # 'should_continue_node' 실행 후, 업데이트된 상태를 보고 분기합니다.
    workflow.add_conditional_edges(
        "should_continue_node",
        lambda state: "end" if state.get("selected_character") == "end" else "node_environment",
        {
            "node_environment": "node_environment",
            "end": END
        }
    )

    # 4. 그래프 컴파일
    return workflow.compile()