from typing import List, TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio
from config import CHARACTERS

# 그래프의 상태(State) 정의
class GraphState(TypedDict):
    story_parts: List[str]  # 지금까지 생성된 이야기 조각들을 리스트로 저장합니다.
    # 발언을 하기 위해 선택된 캐릭터
    selected_character: str

# --- 노드(Node)로 사용할 함수 정의 ---

# 캐릭터 중 누가 행동할지 경쟁하는 비동기 함수
async def _get_character_vote(character_name:str, story_so_far:str) -> Optional[str]:
    """단일 캐릭터의 투표를 비동기적으로 얻는 헬퍼 함수"""
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash",temperature=0)
    prompt = f"""
    당신은 '{character_name}'입니다. 아래 상황을 보고, 당신이 다음 차례에 행동하거나 말하는 것이 적절한지 판단해주세요.

    [상황]
    {story_so_far}

    [판단]
    행동하는 것이 적절하다면 '네', 그렇지 않다면 '아니요' 라고만 대답해주세요.
    """
    try:
        response = await llm.ainvoke(prompt)
        vote = response.content.strip() 
        if "네" in vote:
            print(f"--- {character_name}의 투표: {vote} (선택!) ---")
            return character_name
    except Exception:
        return None
    return None

# 경쟁을 통해 행동할 캐릭터를 선택하는 함수
async def race_for_action(state: GraphState) -> dict:
    """
    모든 캐릭터에게 동시에 물어보고, 가장 먼저 '네'라고 답하는 캐릭터를 선택합니다.
    """
    story_so_far = "".join(state["story_parts"])
    characters = list(CHARACTERS.keys()) # 경쟁에 참여할 캐릭터 목록

    tasks = [asyncio.create_task(_get_character_vote(name, story_so_far)) for name in characters]
    
    winner = None
    
    # asyncio.as_completed는 작업이 완료되는 순서대로 결과를 반환합니다.
    for future in asyncio.as_completed(tasks):
        try:
            result = await future
            if result:  # '네'라고 답한 첫 번째 승자를 찾으면
                winner = result
                break # 즉시 루프를 중단하고 더 이상 기다리지 않습니다.
        except asyncio.CancelledError:
            pass # 취소된 작업은 무시합니다.
            
    # 승자가 결정되었으므로, 아직 실행 중인 나머지 작업들을 모두 취소합니다.
    for task in tasks:
        if not task.done():
            task.cancel()
        
    if not winner:
        print("--- 행동하려는 캐릭터가 없습니다. ---")
        return {"selected_character": "None"}

    return {"selected_character": winner}

def should_continue(state: GraphState):
    """
    사용자 입력에 따라 이야기 생성을 계속할지 결정하고, 그 결과를 상태에 저장합니다.
    이 함수는 이제 노드 역할을 합니다.
    """
    user_input = input("\n계속하시겠습니까? (c/e): ").strip().lower()
    
    if user_input == "c":
        # 다음 엣지에서 사용할 수 있도록 선택을 상태에 저장합니다.
        return {"selected_character": "main_agent"}
    elif user_input == "e":
        return {"selected_character": "end"}
    else:
        print("'c' 또는 'e'를 입력해주세요.")
        return should_continue(state)  # 올바른 입력까지 반복
    
# 환경을 담당하는 메인 에이전트
def node_environment(state: GraphState):
    """
    환경을 담당하는 메인 에이전트 노드
    """
    story_parts = state["story_parts"]
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.7)
    character_names = ", ".join([f"'{name}'" for name in CHARACTERS.keys()]) # 사용 가능한 캐릭터 목록
    prompt = f"""
    당신은 셰익스피어의 소설 '햄릿'의 세상을 simulating하는 simulator입니다. 당신이 생성한 세상을 텍스트로 묘사해주세요. 당신이 묘사한 세상을 바탕으로 {character_names}의 역할을 하는 서브 에이전트들이 이어서 행동할 것입니다. 

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
# 각 캐릭터를 담당하는 서브 에이전트를 생성하는 팩토리 함수
def create_character_agent(character_name: str, character_prompt: str,model_name: str):
    """캐릭터 에이전트 노드 함수를 생성합니다."""
    def character_agent(state: GraphState) -> dict:
        story_parts = state["story_parts"]
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.7)

        prompt = f"""
        {character_prompt}

        [지금까지의 상황]
        {''.join(story_parts)}

        [당신의 다음 행동 또는 대사]
        """

        response = llm.invoke(prompt)
        next_part = f"\n\n**{character_name.capitalize()}**\n{response.content}"

        print(f"\n--- 서브 에이전트 ({character_name.capitalize()}) ---")
        print(next_part)

        return {
            "story_parts": story_parts + [next_part],
        }
    return character_agent

# 캐릭터별 에이전트 노드를 동적으로 생성
character_agents = {
    f"{name}_agent": create_character_agent(name, data["prompt"],data["model"])
    for name, data in CHARACTERS.items()
}

