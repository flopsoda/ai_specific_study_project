import os
from typing import List, TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio
from config import CHARACTERS, MAIN_WRITER_CONFIG, CHARACTER_AGENT_CONFIG
from shared import global_state
from langgraph.graph import END

# ---그래프의 상태(State) 정의---
class GraphState(TypedDict):
    story_parts: List[str]  # 지금까지 생성된 이야기 조각들을 리스트로 저장합니다.
    discussion : list[str]
    selected_character: str
    user_decision: Optional[str]

# [추가] 메인 작가용 LLM 전역 인스턴스 생성
WRITER_LLM = ChatGoogleGenerativeAI(
    model=MAIN_WRITER_CONFIG["model"],
    temperature=MAIN_WRITER_CONFIG["temperature"]
)

# ---토론 내용을 바탕으로 이야기를 작성하는 메인 작가 에이전트---
def main_writer_node(state: GraphState) -> dict:
    """
    지금까지의 이야기와 캐릭터들의 토론 내용을 종합하여 다음 이야기 단락을 작성합니다.
    """
    # [추가] 상태 업데이트
    global_state["current_status"] = "✍️ 메인 작가가 이야기를 집필하고 있습니다..."
    
    print("\n--- 메인 작가 에이전트 작동 ---")
    story_so_far = "".join(state["story_parts"])
    discussion_str = "\n".join(state["discussion"])
    
    # [수정] 전역 인스턴스 WRITER_LLM 사용
    prompt = MAIN_WRITER_CONFIG["prompt_template"].format(
        world_name=MAIN_WRITER_CONFIG["world_name"],
        world_description=MAIN_WRITER_CONFIG["world_description"],
        story_so_far=story_so_far,
        discussion_str=discussion_str
    )
    response = WRITER_LLM.invoke(prompt)
    next_part = response.content.strip()
    print("--- 생성된 장면 ---")
    print(next_part)
    # 생성된 이야기를 story_parts에 추가하고, 다음 사이클을 위해 토론 내용은 비웁니다.
    return {
        "story_parts": state["story_parts"] + ["\n\n" + next_part],
        "discussion": [], 
    }

# --- 노드(Node)로 사용할 함수 정의 ---

## ---캐릭터 중 누가 토론 중 의견을 제시할지 경쟁하는 함수---
VOTE_LLM = ChatGoogleGenerativeAI(
    model = CHARACTER_AGENT_CONFIG["vote_model"],
    temperature=CHARACTER_AGENT_CONFIG["vote_temperature"]
)

# [추가] 의견 생성용 LLM 전역 인스턴스 생성
OPINION_LLM = ChatGoogleGenerativeAI(
    model=CHARACTER_AGENT_CONFIG["opinion_model"],
    temperature=CHARACTER_AGENT_CONFIG["opinion_temperature"]
)

async def _get_character_vote(character_name:str, story_so_far:str, discussion: list[str]) -> Optional[str]:
    """단일 서브 에이전트의 투표를 비동기적으로 얻는 헬퍼 함수"""
    discussion_str = "\n".join(discussion)
    character_config = CHARACTERS[character_name]
    character_prompt = character_config["prompt"]
    prompt = CHARACTER_AGENT_CONFIG["prompt_templates"]["vote"].format(
        character_name=character_name,
        character_prompt=character_prompt,
        story_so_far=story_so_far,
        discussion_str=discussion_str
    )
    try:
        response = await VOTE_LLM.ainvoke(prompt)
        vote = response.content.strip() 
        if "네" in vote:
           # print(f"--- {character_name}의 투표: {vote} (선택!) ---")
            return character_name
    except Exception as e:
        # 오류 발생 시 어떤 캐릭터에서 문제가 있었는지 로그를 남깁니다.
        print(f"--- {character_name} 투표 중 오류 발생: {e} ---")
        return None
    return None

## ---경쟁을 통해 행동할 캐릭터를 선택하는 함수---
async def race_for_action(state: GraphState) -> dict:
    """
    모든 캐릭터에게 동시에 물어보고, 가장 먼저 '네'라고 답하는 캐릭터를 선택합니다.
    """
    # [추가] 상태 업데이트
    global_state["current_status"] = "👀 눈치 게임 중... (누가 발언할지 경쟁 중)"
    
    story_so_far = "".join(state["story_parts"])
    discussion = state["discussion"]
    characters = list(CHARACTERS.keys()) # 경쟁에 참여할 캐릭터 목록
    tasks = [asyncio.create_task(_get_character_vote(name, story_so_far, discussion)) for name in characters] 
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

## ---선택된 캐릭터가 토론에 대한 의견을 생성하는 함수---
def generate_character_opinion(state: GraphState) -> dict:
    """선택된 캐릭터가 토론에 대한 의견을 생성하고 discussion 상태를 업데이트합니다."""
    character_name = state["selected_character"]
    
    # [추가] 상태 업데이트
    global_state["current_status"] = f"🗣️ '{character_name}' 작가가 발언을 정리하는 중..."

    if not character_name or character_name == "None":
        return {}
   # print(f"\n--- 토론 발언: {character_name} ---")
    story_so_far = "".join(state["story_parts"])
    discussion = state["discussion"]
    discussion_str = "\n".join(discussion)
    # 캐릭터 설정 가져오기
    character_config = CHARACTERS[character_name]
    
    # [수정] 전역 인스턴스 OPINION_LLM 사용
    prompt = CHARACTER_AGENT_CONFIG["prompt_templates"]["generate_opinion"].format(
        character_name=character_name,
        character_prompt=character_config["prompt"],
        story_so_far=story_so_far,
        discussion_str=discussion_str
    )
    response = OPINION_LLM.invoke(prompt)
    opinion = f"**{character_name} specialist writer**: {response.content.strip()}" 
    print(opinion)
    # 생성된 의견을 discussion 리스트에 추가
    return {"discussion": discussion + [opinion]}

# [수정됨] 사용자 입력을 비동기로 기다리는 노드
async def check_continuation(state: GraphState):
    print("\n⏳ 웹 브라우저에서 [계속하기] 또는 [종료]를 선택하기를 기다리는 중...")
    
    # [추가] 상태 업데이트
    global_state["current_status"] = "⏳ 당신의 선택을 기다리고 있습니다."

    # 1. 웹 UI에 버튼을 띄우라고 신호를 보냄
    global_state["waiting_for_input"] = True
    global_state["user_decision"] = None # 이전 결정 초기화

    # 2. 웹에서 버튼을 누를 때까지 무한 대기 (0.5초 간격 체크)
    while global_state["user_decision"] is None:
        await asyncio.sleep(0.5)

    # 3. 결정이 내려지면 신호를 끄고 진행
    decision = global_state["user_decision"]
    global_state["waiting_for_input"] = False
    
    print(f"✅ 사용자 선택 확인: {decision}")
    
    # state에 결정을 저장해서 라우터가 판단하게 함 (선택 사항)
    return {"user_decision": decision}

# [추가됨] 라우팅 로직
def route_continuation(state: GraphState):
    # check_continuation 노드에서 결정된 사항을 global_state에서 확인
    decision = global_state.get("user_decision")
    
    if decision == "continue":
        return "race_for_action"
    else:
        return END








