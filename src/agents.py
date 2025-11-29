from cmath import phase
import os
from typing import List, TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio

from config import CHARACTERS, MAIN_WRITER_CONFIG, CHARACTER_AGENT_CONFIG, JUDGE_CONFIG 
from shared import global_state
from langgraph.graph import END
from utils import get_story_context
from memory import lore_book


# --- 그래프의 상태(State) 정의 ---
class GraphState(TypedDict):
    # 기본 필드
    story_parts: List[str]
    current_context: str
    retrieved_memory: str
    discussion: List[str]
    selected_character: str
    user_decision: Optional[str]
    # 초안/비평 순환 관련 필드
    draft: Optional[str]
    revision_history: List[str]
    revision_count: int
    phase: str                       # "ideation" | "critique"
    judge_result: Optional[str]      # "pass" | "revise"


# --- LLM 전역 인스턴스 생성 ---
WRITER_LLM = ChatGoogleGenerativeAI(
    model=MAIN_WRITER_CONFIG["model"],
    temperature=MAIN_WRITER_CONFIG["temperature"]
)

JUDGE_LLM = ChatGoogleGenerativeAI(
    model=JUDGE_CONFIG["model"],
    temperature=JUDGE_CONFIG["temperature"]
)

VOTE_LLM = ChatGoogleGenerativeAI(
    model=CHARACTER_AGENT_CONFIG["vote_model"],
    temperature=CHARACTER_AGENT_CONFIG["vote_temperature"]
)

OPINION_LLM = ChatGoogleGenerativeAI(
    model=CHARACTER_AGENT_CONFIG["opinion_model"],
    temperature=CHARACTER_AGENT_CONFIG["opinion_temperature"]
)


# --- 노드 함수 정의 ---

# --- 사용자 입력 대기 노드 ---
async def check_continuation(state: GraphState):
    """웹 UI에서 사용자의 선택(계속/종료)을 기다립니다."""
    global_state["current_node"] = "user_input"
    global_state["current_status"] = "당신의 선택을 기다리고 있습니다."
    global_state["waiting_for_input"] = True
    global_state["user_decision"] = None 
    global_state["user_instruction"] = None
    
    print("\n⏳ 웹 브라우저에서 [계속하기] 또는 [종료]를 선택하기를 기다리는 중...")

    # 웹에서 버튼을 누를 때까지 대기
    while global_state["user_decision"] is None:
        await asyncio.sleep(0.5)

    decision = global_state["user_decision"]
    instruction = global_state.get("user_instruction", "")
    global_state["waiting_for_input"] = False
    
    print(f"✅ 사용자 선택 확인: {decision}")
    if instruction:
        print(f"사용자 개입: {instruction}")
    
    if decision == "continue":
        new_discussion = []
        if instruction:
            system_msg = f"*** [긴급 상황 발생] 외부의 절대적인 힘에 의해 다음 현상이 발생했습니다: '{instruction}' ***\n(모든 작가는 이 상황을 최우선으로 반영하여 다음 전개를 논의하십시오.)"
            new_discussion.append(system_msg)
        
        # 새 문단 사이클 시작 → 상태 초기화
        return {
            "user_decision": decision,
            "discussion": new_discussion,
            "draft": None,
            "revision_history": [],
            "revision_count": 0,
            "phase": "ideation",
            "judge_result": None
        }
        
    return {"user_decision": decision}


# --- 라우팅 함수 ---
def route_continuation(state: GraphState):
    """사용자 선택에 따라 다음 노드를 결정합니다."""
    decision = global_state.get("user_decision")
    
    if decision == "continue":
        return "race_for_action"
    else:
        return END


# --- RAG 메모리 검색 노드 ---
def retrieve_memory_node(state: GraphState) -> dict:
    """이번 턴에 필요한 과거 기억을 LoreBook에서 검색합니다."""
    global_state["current_node"] = "memory"
    print("\n[System] 이번 턴에 필요한 과거 기억을 검색합니다...")
    
    query = state.get("current_context", "")
    if not query:
        query = get_story_context(state["story_parts"])
        
    memory = lore_book.search_relevant_info(query)
    
    if memory and "아직 기록된" not in memory:
        print(f"🔍 검색된 기억: {memory[:50]}...")
    else:
        print("🔍 검색된 기억 없음 (초반이거나 데이터 부족)")
        
    return {"retrieved_memory": memory}


# --- 발언권 경쟁 헬퍼 함수 ---
async def _get_character_vote(
    character_name: str, 
    story_so_far: str, 
    discussion: List[str], 
    context: str, 
    phase: str, 
    draft: str, 
    revision_history_str: str
) -> Optional[str]:
    """단일 캐릭터의 투표를 비동기적으로 얻는 헬퍼 함수"""
    discussion_str = "\n".join(discussion)
    character_config = CHARACTERS[character_name]
    character_prompt = character_config["prompt"]

    # phase에 따라 다른 프롬프트 사용
    if phase == "ideation":
        prompt = CHARACTER_AGENT_CONFIG["prompt_templates"]["vote"].format(
            character_name=character_name,
            character_prompt=character_prompt,
            context=context,
            story_so_far=story_so_far,
            discussion_str=discussion_str
        )
    else:  # critique
        prompt = CHARACTER_AGENT_CONFIG["prompt_templates"]["vote_critique"].format(
            character_name=character_name,
            character_prompt=character_prompt,
            context=context,
            story_so_far=story_so_far,
            draft=draft,
            discussion_str=discussion_str,
            revision_history_str=revision_history_str
        )
    
    try:
        response = await VOTE_LLM.ainvoke(prompt)
        vote = response.content.strip() 
        if "네" in vote:
            return character_name
    except Exception as e:
        print(f"--- {character_name} 투표 중 오류 발생: {e} ---")
        return None
    return None


# --- 발언권 경쟁 노드 ---
async def race_for_action(state: GraphState) -> dict:
    """모든 캐릭터에게 동시에 물어보고, 가장 먼저 '네'라고 답하는 캐릭터를 선택합니다."""
    global_state["current_node"] = "race_for_action"
    
    phase = state.get("phase", "ideation")
    phase_display = "1차 회의 (아이디어)" if phase == "ideation" else "비평 회의"
    global_state["current_status"] = f"👀 [{phase_display}] 누가 발언할지 경쟁 중)"
    global_state["phase"] = phase

    story_so_far = state.get("current_context", "")
    context = state.get("retrieved_memory", "")
    draft = state.get("draft", "")
    revision_history = state.get("revision_history", [])
    revision_history_str = "\n---\n".join(revision_history) if revision_history else "(이전 비평 없음)"
    discussion = state["discussion"]
        
    characters = list(CHARACTERS.keys())
    tasks = [
        asyncio.create_task(
            _get_character_vote(name, story_so_far, discussion, context, phase, draft, revision_history_str)
        ) 
        for name in characters
    ]
    
    winner = None
    for future in asyncio.as_completed(tasks):
        try:
            result = await future
            if result:
                winner = result
                break
        except asyncio.CancelledError:
            pass
    
    # 승자가 결정되면 나머지 작업 취소
    for task in tasks:
        if not task.done():
            task.cancel()
            
    if not winner:
        print("--- 행동하려는 캐릭터가 없습니다. ---")
        return {"selected_character": "None"}
    
    return {"selected_character": winner}


# --- 캐릭터 의견 생성 노드 ---
def generate_character_opinion(state: GraphState) -> dict:
    """선택된 캐릭터가 토론에 대한 의견을 생성합니다."""
    global_state["current_node"] = "generate_opinion"
    
    character_name = state["selected_character"]
    phase = state.get("phase", "ideation")
    phase_display = "1차 회의" if phase == "ideation" else "비평 회의"
    global_state["current_status"] = f"🗣️ [{phase_display}] '{character_name}' 작가가 발언을 정리하는 중..."

    if not character_name or character_name == "None":
        return {}

    story_so_far = state.get("current_context", "")
    context = state.get("retrieved_memory", "")
    discussion = state["discussion"]
    discussion_str = "\n".join(discussion)
    character_config = CHARACTERS[character_name]
    
    draft = state.get("draft", "")
    revision_history = state.get("revision_history", [])
    revision_history_str = "\n---\n".join(revision_history) if revision_history else "(이전 비평 없음)"
    
    # phase에 따라 다른 프롬프트 사용
    if phase == "ideation":
        prompt = CHARACTER_AGENT_CONFIG["prompt_templates"]["generate_opinion"].format(
            character_name=character_name,
            character_prompt=character_config["prompt"],
            context=context,
            story_so_far=story_so_far,
            discussion_str=discussion_str
        )
    else:  # critique
        prompt = CHARACTER_AGENT_CONFIG["prompt_templates"]["generate_opinion_critique"].format(
            character_name=character_name,
            character_prompt=character_config["prompt"],
            context=context,
            story_so_far=story_so_far,
            draft=draft,
            discussion_str=discussion_str,
            revision_history_str=revision_history_str
        )

    response = OPINION_LLM.invoke(prompt)
    opinion = f"[{character_name} 파트 담당 작가]: {response.content.strip()}" 
    print(opinion)
    
    return {"discussion": discussion + [opinion]}


# --- 메인 작가 노드 ---
def main_writer_node(state: GraphState) -> dict:
    """지금까지의 회의 내용을 종합하여 초안을 작성하거나 수정합니다."""
    global_state["current_node"] = "main_writer"
    print("\n--- 메인 작가 에이전트 작동 ---")
    
    phase = state.get("phase", "ideation")
    story_so_far = state.get("current_context", "")
    context = state.get("retrieved_memory", "")
    discussion_str = "\n".join(state["discussion"])
    
    # phase에 따라 다른 프롬프트 사용
    if phase == "ideation":
        global_state["current_status"] = "메인 작가가 초안을 작성하고 있습니다..."
        print("\n--- 메인 작가: 초안 작성 중 ---")
        
        prompt = MAIN_WRITER_CONFIG["prompt_template"].format(
            world_name=MAIN_WRITER_CONFIG["world_name"],
            world_description=MAIN_WRITER_CONFIG["world_description"],
            context=context,
            story_so_far=story_so_far,
            discussion_str=discussion_str
        )
    else:
        global_state["current_status"] = "메인 작가가 초안을 수정하고 있습니다..."
        print("\n--- 메인 작가: 초안 수정 중 ---")
        
        prompt = MAIN_WRITER_CONFIG["prompt_template_revise"].format(
            world_name=MAIN_WRITER_CONFIG["world_name"],
            world_description=MAIN_WRITER_CONFIG["world_description"],
            context=context,
            story_so_far=story_so_far,
            current_draft=state.get("draft", ""),
            critique_str=discussion_str
        )

    response = WRITER_LLM.invoke(prompt)
    new_draft = response.content.strip()
    new_draft = new_draft.replace("[수정된 이야기]", "").strip()
    print(f"\n[메인 작가] 결과:\n{new_draft[:100]}...\n")
    
    # revision_history는 비평 회의(critique) 내용만 누적
    current_history = state.get("revision_history", [])
    if phase == "critique":
        updated_history = current_history + state["discussion"]
    else:
        updated_history = current_history
    
    # 웹 대시보드 업데이트
    global_state["draft"] = new_draft
    global_state["revision_count"] = state.get("revision_count", 0) + 1
    
    return {
        "draft": new_draft,
        "revision_history": updated_history,
        "discussion": [],
        "phase": "critique",
        "revision_count": state.get("revision_count", 0) + 1
    }


# --- 심사 노드 ---
def judge_node(state: GraphState) -> dict:
    """비평 회의 결과를 검토하고 통과 또는 수정 필요 여부를 판단합니다."""
    global_state["current_node"] = "judge"
    global_state["current_status"] = "편집장이 초안을 심사 중..."
    print("\n--- 편집장: 초안 심사 중 ---")
    
    draft = state.get("draft", "")
    discussion = state.get("discussion", [])
    critique_str = "\n".join(discussion) if discussion else "(비평 없음 - 모두 만족)"
    
    # 비평 회의에서 아무도 발언 안 했으면 자동 통과
    if not discussion:
        print("[편집장] 비평 회의에서 이의 없음 → 자동 통과!")
        return {"judge_result": "pass"}
    
    prompt = JUDGE_CONFIG["prompt_template"].format(
        draft=draft,
        critique_str=critique_str
    )
    
    response = JUDGE_LLM.invoke(prompt)
    result = response.content.strip()
    
    if "통과" in result:
        print("[편집장] 초안 승인!")
        return {"judge_result": "pass"}
    else:
        print("[편집장] 수정 필요")
        return {"judge_result": "revise"}


# --- 문단 확정 노드 ---
def finalize_node(state: GraphState) -> dict:
    """심사를 통과한 draft를 story_parts에 추가하고, 상태를 초기화합니다."""
    global_state["current_node"] = "finalize"
    global_state["current_status"] = "문단 확정 및 저장 중..."
    print("\n--- 문단 확정: 이야기에 추가 ---")
    
    draft = state.get("draft", "")
    story_parts = state.get("story_parts", [])
    
    new_story_parts = story_parts + [draft]
    new_context = get_story_context(new_story_parts)
    
    # 웹 대시보드 업데이트
    global_state["story_parts"] = new_story_parts
    global_state["discussion"] = []
    global_state["draft"] = None
    
    # LoreBook에 저장 (RAG)
    lore_book.check_and_archive(new_story_parts)
    
    print(f"현재까지 {len(new_story_parts)}개의 문단이 작성되었습니다.")
    
    return {
        "story_parts": new_story_parts,
        "current_context": new_context,
        "draft": None,
        "revision_history": [],
        "revision_count": 0,
        "phase": "ideation",
        "judge_result": None,
        "discussion": []
    }








