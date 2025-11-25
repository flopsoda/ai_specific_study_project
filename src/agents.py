from cmath import phase
import os
from typing import List, TypedDict, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
import asyncio
from config import CHARACTERS, MAIN_WRITER_CONFIG, CHARACTER_AGENT_CONFIG, JUDGE_CONFIG 
from shared import global_state
from langgraph.graph import END
from utils import get_story_context
from memory import lore_book # [추가]

# ---그래프의 상태(State) 정의---
class GraphState(TypedDict):
    story_parts: List[str]
    current_context: str
    retrieved_memory: str   # [추가] 이번 턴에 사용할 과거 기억 (RAG 결과)
    discussion : list[str]
    selected_character: str
    user_decision: Optional[str]
    draft: Optional[str]             # 현재 작성 중인 초안
    revision_history: List[str]      # 이번 문단의 전체 회의 기록
    revision_count: int              # 수정 횟수
    phase: str                       # "ideation" | "critique"
    judge_result: Optional[str]      # "pass" | "revise" (라우팅에 사용)

# [추가] 메인 작가용 LLM 전역 인스턴스 생성
WRITER_LLM = ChatGoogleGenerativeAI(
    model=MAIN_WRITER_CONFIG["model"],
    temperature=MAIN_WRITER_CONFIG["temperature"]
)
JUDGE_LLM = ChatGoogleGenerativeAI(
    model=JUDGE_CONFIG["model"],
    temperature=JUDGE_CONFIG["temperature"]
)
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

# ---토론 내용을 바탕으로 이야기를 작성하는 메인 작가 에이전트---
def main_writer_node(state: GraphState) -> dict:
    """
    지금까지의 이야기와 캐릭터들의 토론 내용을 종합하여 다음 이야기 단락을 작성합니다.
    """
    print("\n--- 메인 작가 에이전트 작동 ---")
    
    phase = state.get("phase","ideation")
    story_so_far = state.get("current_context", "")
    context = state.get("retrieved_memory", "") # [추가] 메모리 가져오기
    discussion_str = "\n".join(state["discussion"])
    
    # --- phase에 따라 다른 프롬프트 사용 ---
    if phase == "ideation":
        # 1차 회의 후: 초안 작성
        global_state["current_status"] = "✍️ 메인 작가가 초안을 작성하고 있습니다..."
        print("\n--- 메인 작가: 초안 작성 중 ---")
        
        prompt = MAIN_WRITER_CONFIG["prompt_template"].format(
            world_name=MAIN_WRITER_CONFIG["world_name"],
            world_description=MAIN_WRITER_CONFIG["world_description"],
            context=context,
            story_so_far=story_so_far,
            discussion_str=discussion_str
        )
    else:
        # 비평 회의 후: 수정
        global_state["current_status"] = "✍️ 메인 작가가 초안을 수정하고 있습니다..."
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
    print(f"\n[메인 작가] 결과:\n{new_draft[:100]}...\n")
    
    # --- 핵심: story_parts는 건드리지 않음! draft에만 저장 ---
    # revision_history에 현재 회의 내용 누적
    current_history = state.get("revision_history", [])

# phase가 critique일 때만 회의 내용을 히스토리에 추가
    if phase == "critique":
        updated_history = current_history + state["discussion"]
    else:
        updated_history = current_history  # ideation 회의는 저장 안 함

    return {
    "draft": new_draft,
    "revision_history": updated_history,
    "discussion": [],
    "phase": "critique",
    "revision_count": state.get("revision_count", 0) + 1
    }

# --- 노드(Node)로 사용할 함수 정의 ---

# --- 1. 투표 헬퍼 함수 수정 ---
async def _get_character_vote(character_name:str, story_so_far:str, discussion: list[str],context: str, phase : str,draft: str,revision_history_str:str) -> Optional[str]:
    """단일 서브 에이전트의 투표를 비동기적으로 얻는 헬퍼 함수"""
    discussion_str = "\n".join(discussion)
    character_config = CHARACTERS[character_name]
    character_prompt = character_config["prompt"]

    # --- phase에 따라 다른 프롬프트 사용 ---
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
    phase = state.get("phase", "ideation")
    phase_display = "1차 회의 (아이디어)" if phase == "ideation" else "비평 회의"

    global_state["current_status"] = f"👀 [{phase_display}] 눈치 게임 중... (누가 발언할지 경쟁 중)"
    global_state["phase"] = phase  # 웹 UI에서 표시용

    # [수정] 매번 계산하지 않고, State에 저장된 값을 바로 사용
    story_so_far = state.get("current_context", "")
    context = state.get("retrieved_memory", "")
    draft = state.get("draft", "")
    revision_history = state.get("revision_history", [])
    revision_history_str = "\n---\n".join(revision_history) if revision_history else "(이전 비평 없음)"
    
    discussion = state["discussion"]
    # [검증용 로그] 실제로 비워졌는지 터미널에서 확인
    print(f"\n[DEBUG] 현재 토론 내역 개수: {len(discussion)}개")
    if len(discussion) > 0:
        print(f"[DEBUG] 잔여 데이터 확인: {discussion[0][:30]}...")
    else:
        print("[DEBUG] 토론 내역이 깨끗하게 비어있습니다.")
        
    characters = list(CHARACTERS.keys()) # 경쟁에 참여할 캐릭터 목록
    # _get_character_vote 호출 시 context 전달
    tasks = [asyncio.create_task(_get_character_vote(name, story_so_far, discussion, context, phase, draft, revision_history_str)) for name in characters]
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
    phase = state.get("phase", "ideation")
    phase_display = "1차 회의" if phase == "ideation" else "비평 회의"
    
    global_state["current_status"] = f"🗣️ [{phase_display}] '{character_name}' 작가가 발언을 정리하는 중..."

    if not character_name or character_name == "None":
        return {}

    # [수정] 매번 계산하지 않고, State에 저장된 값을 바로 사용
    story_so_far = state.get("current_context", "")
    context = state.get("retrieved_memory", "") # [추가] 메모리 가져오기
    
    discussion = state["discussion"]
    discussion_str = "\n".join(discussion)
    
    # 캐릭터 설정 가져오기
    character_config = CHARACTERS[character_name]
    
    draft = state.get("draft", "")
    revision_history = state.get("revision_history", [])
    revision_history_str = "\n---\n".join(revision_history) if revision_history else "(이전 비평 없음)"
    
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
    # 생성된 의견을 discussion 리스트에 추가
    return {"discussion": discussion + [opinion]}

# [수정됨] 사용자 입력을 비동기로 기다리는 노드
async def check_continuation(state: GraphState):
    print("\n⏳ 웹 브라우저에서 [계속하기] 또는 [종료]를 선택하기를 기다리는 중...")
    
    global_state["current_status"] = "⏳ 당신의 선택을 기다리고 있습니다."

    # 1. 웹 UI에 버튼을 띄우라고 신호를 보냄
    global_state["waiting_for_input"] = True
    global_state["user_decision"] = None 
    global_state["user_instruction"] = None # 초기화

    # 2. 웹에서 버튼을 누를 때까지 무한 대기
    while global_state["user_decision"] is None:
        await asyncio.sleep(0.5)

    # 3. 결정이 내려지면 신호를 끄고 진행
    decision = global_state["user_decision"]
    instruction = global_state.get("user_instruction", "") # 사용자 입력 가져오기

    global_state["waiting_for_input"] = False
    
    print(f"✅ 사용자 선택 확인: {decision}")
    if instruction:
        print(f"사용자 개입: {instruction}")
    
    if decision == "continue":
        new_discussion = []
        if instruction:
            system_msg = f"*** [긴급 상황 발생] 외부의 절대적인 힘에 의해 다음 현상이 발생했습니다: '{instruction}' ***\n(모든 작가는 이 상황을 최우선으로 반영하여 다음 전개를 논의하십시오.)"
            new_discussion.append(system_msg)
        
        # [핵심] 새 문단 사이클 시작 → 상태 초기화
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

# --- 심사 노드: 비평 회의 결과를 보고 통과/반려 결정 ---
def judge_node(state: GraphState) -> dict:
    """
    비평 회의 결과를 검토하고 통과 또는 수정 필요 여부를 판단합니다.
    """
    global_state["current_status"] = "🧐 편집장이 초안을 심사 중..."
    print("\n--- 편집장: 초안 심사 중 ---")
    
    draft = state.get("draft", "")
    discussion = state.get("discussion", [])
    critique_str = "\n".join(discussion) if discussion else "(비평 없음 - 모두 만족)"
    
    # 비평 회의에서 아무도 발언 안 했으면 → 자동 통과
    if not discussion:
        print("✅ [편집장] 비평 회의에서 이의 없음 → 자동 통과!")
        return {"judge_result": "pass"}
    
    prompt = JUDGE_CONFIG["prompt_template"].format(
        draft=draft,
        critique_str=critique_str
    )
    
    response = JUDGE_LLM.invoke(prompt)
    result = response.content.strip()
    
    if "통과" in result:
        print("✅ [편집장] 초안 승인!")
        return {"judge_result": "pass"}
    else:
        print(f"❌ [편집장] 수정 필요")
        return {"judge_result": "revise"}
# --- 문단 확정 노드: draft를 story_parts에 추가 ---
def finalize_node(state: GraphState) -> dict:
    """
    심사를 통과한 draft를 story_parts에 추가하고, 상태를 초기화합니다.
    """
    global_state["current_status"] = "🎉 문단 확정 및 저장 중..."
    print("\n--- 문단 확정: 이야기에 추가 ---")
    
    draft = state.get("draft", "")
    story_parts = state.get("story_parts", [])
    
    # draft를 story_parts에 추가
    new_story_parts = story_parts + [draft]
    new_context = get_story_context(new_story_parts)
    
    # 웹 대시보드 업데이트
    global_state["story_parts"] = new_story_parts
    global_state["discussion"] = []
    global_state["draft"] = None
    
    # LoreBook에 저장 (RAG)
    lore_book.check_and_archive(new_story_parts)
    
    print(f"📚 현재까지 {len(new_story_parts)}개의 문단이 작성되었습니다.")
    
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
 
# [추가됨] 라우팅 로직
def route_continuation(state: GraphState):
    # check_continuation 노드에서 결정된 사항을 global_state에서 확인
    decision = global_state.get("user_decision")
    
    if decision == "continue":
        return "race_for_action"
    else:
        return END

# [신규] 토론 시작 전, 관련 기억을 검색하여 State에 저장하는 노드
def retrieve_memory_node(state: GraphState) -> dict:
    print("\n🧠 [System] 이번 턴에 필요한 과거 기억을 검색합니다...")
    
    # 검색 쿼리는 현재 컨텍스트(최근 이야기)를 사용
    query = state.get("current_context", "")
    if not query:
        query = get_story_context(state["story_parts"])
        
    # LoreBook에서 검색
    memory = lore_book.search_relevant_info(query)
    
    if memory and "아직 기록된" not in memory:
        print(f"🔍 검색된 기억: {memory[:50]}...")
    else:
        print("🔍 검색된 기억 없음 (초반이거나 데이터 부족)")
        
    return {"retrieved_memory": memory}








