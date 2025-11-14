import os
from typing import List, TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio
from config import CHARACTERS, MAIN_WRITER_CONFIG, CHARACTER_AGENT_CONFIG

# ---그래프의 상태(State) 정의---
class GraphState(TypedDict):
    story_parts: List[str]  # 지금까지 생성된 이야기 조각들을 리스트로 저장합니다.
    discussion : list[str]
    selected_character: str

# ---토론 내용을 바탕으로 이야기를 작성하는 메인 작가 에이전트---
def main_writer_node(state: GraphState) -> dict:
    """
    지금까지의 이야기와 캐릭터들의 토론 내용을 종합하여 다음 이야기 단락을 작성합니다.
    """
    print("\n--- 메인 작가 에이전트 작동 ---")
    story_so_far = "".join(state["story_parts"])
    discussion_str = "\n".join(state["discussion"])
    # 메인 작가용 LLM 설정
    llm = ChatGoogleGenerativeAI(
        model=MAIN_WRITER_CONFIG["model"],
        temperature=MAIN_WRITER_CONFIG["temperature"]
        )
    prompt = MAIN_WRITER_CONFIG["prompt_template"].format(
        world_name=MAIN_WRITER_CONFIG["world_name"],
        world_description=MAIN_WRITER_CONFIG["world_description"],
        story_so_far=story_so_far,
        discussion_str=discussion_str
    )
    response = llm.invoke(prompt)
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
    if not character_name or character_name == "None":
        return {}
   # print(f"\n--- 토론 발언: {character_name} ---")
    story_so_far = "".join(state["story_parts"])
    discussion = state["discussion"]
    discussion_str = "\n".join(discussion)
    # 캐릭터 설정 가져오기
    character_config = CHARACTERS[character_name]
    llm = ChatGoogleGenerativeAI(
        model=CHARACTER_AGENT_CONFIG["opinion_model"],
        temperature=CHARACTER_AGENT_CONFIG["opinion_temperature"]
        )
    prompt = CHARACTER_AGENT_CONFIG["prompt_templates"]["generate_opinion"].format(
        character_name=character_name,
        character_prompt=character_config["prompt"],
        story_so_far=story_so_far,
        discussion_str=discussion_str
    )
    response = llm.invoke(prompt)
    opinion = f"**{character_name} specialist writer**: {response.content.strip()}" 
    print(opinion)
    # 생성된 의견을 discussion 리스트에 추가
    return {"discussion": discussion + [opinion]}

## ---사용자에게 계속 할 것인지 묻는 노드---
def should_continue(state: GraphState):
    """
    사용자 입력에 따라 이야기 생성을 계속할지 결정하고, 그 결과를 상태에 저장합니다.
    이 함수는 이제 노드 역할을 합니다.
    """
    user_input = input("\n계속하시겠습니까? (c/e): ").strip().lower()  
    if user_input == "c":
        print("\n---토론 시작---")
        # 다음 엣지에서 사용할 수 있도록 선택을 상태에 저장합니다.
        return {"selected_character": "start_discussion"}
    elif user_input == "e":
        return {"selected_character": "end"}
    else:
        print("'c' 또는 'e'를 입력해주세요.")
        return should_continue(state)  # 올바른 입력까지 반복




    



