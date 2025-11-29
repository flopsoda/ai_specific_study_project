import os
import asyncio
import threading
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()
os.environ["GRPC_VERBOSITY"] = "NONE" 
os.environ["GRPC_TRACE"] = ""

from graph import build_graph
from agents import GraphState
from config import STORY_CONFIG
from server import start_server
from shared import global_state
from utils import get_story_context


# --- 그래프 실행 ---
async def main():
    # 1. 웹 서버를 백그라운드 스레드에서 시작
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    print("\n🌐 웹 모니터링 주소: http://127.0.0.1:8000")
    print("   (브라우저를 열어 진행 상황을 실시간으로 확인하세요)\n")

    # 2. 그래프 빌드
    app = build_graph()
    
    # 3. 초기 상태 설정
    initial_prompt = STORY_CONFIG["initial_prompt"]
    initial_story_parts = [initial_prompt]
    initial_context = get_story_context(initial_story_parts)

    initial_state: GraphState = {
        # 기본 필드
        "story_parts": initial_story_parts,
        "current_context": initial_context,
        "retrieved_memory": "",
        "discussion": [], 
        "selected_character": "",
        "user_decision": None,
        # 초안/비평 순환 관련 필드
        "draft": None,
        "revision_history": [],
        "revision_count": 0,
        "phase": "ideation",
        "judge_result": None,
    }
    
    # 4. 초기 상태를 웹 공유 변수에 반영
    global_state["story_parts"] = initial_state["story_parts"]
    global_state["discussion"] = initial_state["discussion"]
    global_state["phase"] = initial_state["phase"]
    global_state["draft"] = initial_state["draft"]
    global_state["revision_count"] = initial_state["revision_count"]

    # 5. 그래프 실행
    config = {"recursion_limit": STORY_CONFIG["recursion_limit"]} 
    print("--- 이야기 생성을 시작합니다 ---")

    async for event in app.astream(initial_state, config=config):
        for node_name, state_update in event.items():
            if state_update is None:
                continue
            # 상태 업데이트가 있으면 공유 변수에 반영
            if "story_parts" in state_update:
                global_state["story_parts"] = state_update["story_parts"]
            if "discussion" in state_update:
                global_state["discussion"] = state_update["discussion"]

    # 6. 최종 결과 출력
    print("\n--- 최종 결과물 ---")
    print("\n---\n".join(global_state['story_parts']))


if __name__ == "__main__":
    asyncio.run(main())