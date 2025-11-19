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

# --- 그래프 실행 ---
async def main():
    # 1. 웹 서버를 백그라운드 스레드에서 시작
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    print("\n🌐 웹 모니터링 주소: http://127.0.0.1:8000")
    print("   (브라우저를 열어 진행 상황을 실시간으로 확인하세요)\n")

    app = build_graph()
    
    # 그래프 실행 설정
    initial_prompt = STORY_CONFIG["initial_prompt"]
    initial_state: GraphState = {
        "story_parts": [initial_prompt],
        "discussion": [], 
        "selected_character": ""
    }
    
    # 초기 상태를 웹 공유 변수에 반영
    global_state["story_parts"] = initial_state["story_parts"]
    global_state["discussion"] = initial_state["discussion"]

    config = {"recursion_limit": STORY_CONFIG["recursion_limit"]} 
    
    print("--- 이야기 생성을 시작합니다 (콘솔에서 입력 대기 시 입력해주세요) ---")

    # ainvoke 대신 astream을 사용하여 단계별 상태 변화를 감지합니다.
    async for event in app.astream(initial_state, config=config):
        # event는 각 노드의 실행 결과(Dict)를 담고 있습니다.
        for node_name, state_update in event.items():
            if state_update is None:
                continue
            # 상태 업데이트가 있으면 공유 변수에 반영
            if "story_parts" in state_update:
                global_state["story_parts"] = state_update["story_parts"]
            if "discussion" in state_update:
                global_state["discussion"] = state_update["discussion"]
            
            # (선택 사항) 콘솔에도 진행 상황 간단 출력
            # print(f"[{node_name}] 완료")

    print("\n--- 최종 결과물 ---")
    print("".join(global_state['story_parts']))

if __name__ == "__main__":
    asyncio.run(main())