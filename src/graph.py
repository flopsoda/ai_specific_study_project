from typing import List, TypedDict

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import END, StateGraph


# --- 1. 그래프의 상태(State) 정의 ---
class GraphState(TypedDict):
    story_parts: List[str]  # 지금까지 생성된 이야기 조각들을 리스트로 저장합니다.


# --- 2. 노드(Node)로 사용할 함수 정의 ---
def call_main_agent(state: GraphState):
    """
    메인 에이전트 노드입니다. Gemini API를 호출하여 다음 이야기 조각을 생성합니다.
    """
    story_parts = state["story_parts"]
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)
    prompt = f"""
    당신은 장면을 묘사하는 뛰어난 소설가입니다. 이 세계는 21세기 한국입니다. 이전 장면을 이어서 다음 장면을 한두 문장으로 묘사해주세요.
    등장인물의 대사나 행동은 추가하지 말고, 오직 주변 상황과 배경 묘사에만 집중해주세요.

    [이전 장면]
    {''.join(story_parts)}

    [다음 장면 묘사]
    """

    response = llm.invoke(prompt)
    next_part = response.content

    print(f"--- 생성된 장면---")
    print(next_part)

    return {
        "story_parts": story_parts + [next_part],
    }


def call_hamlet_agent(state: GraphState):
    """
    서브 에이전트: 햄릿 캐릭터의 반응을 담당합니다.
    """
    story_parts = state["story_parts"]
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash-exp", temperature=0.7)

    prompt = f"""
    당신은 윌리엄 셰익스피어의 작품 '햄릿'의 '햄릿'입니다. 지금까지의 상황에서 햄릿이 어떻게 행동하고 반응할지 한두 문장으로 작성하세요.
    햄릿의 관점에서 행동, 대사, 생각을 표현해주세요.

    [지금까지의 상황]
    {''.join(story_parts)}

    [햄릿의 반응]
    """

    response = llm.invoke(prompt)
    next_part = response.content

    print(f"\n---  서브 에이전트 (햄릿) ---")
    print(next_part)

    return {
        "story_parts": story_parts + [next_part],
    }


# --- 3. 조건부 엣지(Edge)로 사용할 함수 정의 ---
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


# --- 4. 그래프 구성 및 컴파일 ---
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