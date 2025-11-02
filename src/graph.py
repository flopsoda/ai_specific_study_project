from typing import List, TypedDict
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph
from agents import GraphState, call_main_agent, call_hamlet_agent


# --- 2. 조건부 엣지(Edge)로 사용할 함수 정의 ---
def should_continue(state: GraphState):
    """
    사용자 입력에 따라 이야기 생성을 계속할지 결정하는 조건부 엣지입니다.
    """
    user_input = input("\n계속하시겠습니까? (continue/end): ").strip().lower()
    
    if user_input == "continue":
        return "continue"
    elif user_input == "end":
        return "end"
    else:
        print("'continue' 또는 'end'를 입력해주세요.")
        return should_continue(state)  # 올바른 입력까지 반복


# --- 3. 그래프 구성 및 컴파일 ---
def build_graph():
    workflow = StateGraph(GraphState)
    workflow.add_node("main_agent", call_main_agent)
    workflow.add_node("hamlet_agent", call_hamlet_agent)
    workflow.set_entry_point("main_agent")
    workflow.add_edge("main_agent", "hamlet_agent")
    workflow.add_conditional_edges(
        "hamlet_agent",
        should_continue,
        {
            "continue": "main_agent",
            "end": END
        }
    )
    return workflow.compile()