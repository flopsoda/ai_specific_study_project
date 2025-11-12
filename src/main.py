import os
os.environ["GRPC_VERBOSITY"] = "NONE" 
os.environ["GRPC_TRACE"] = ""
import asyncio
from dotenv import load_dotenv
from graph import build_graph
from agents import GraphState

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- 그래프 실행 ---
async def main():
    app = build_graph()
    
    # 그래프 시각화 
    try:
        img_data = app.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(img_data)
        print("그래프 이미지가 'graph.png'로 저장되었습니다.")
    except Exception as e:
        print(f"그래프 시각화 실패: {e}")
    

    # 그래프 실행
    initial_prompt = "21century of Korea, Hamlet and Ophelia are living in this modern world."
    initial_state: GraphState = {"story_parts": [initial_prompt],"discussion" : [], "selected_character": ""}
    # 재귀 제한을 늘려서 config를 설정합니다.
    config = {"recursion_limit": 100} 
    final_state = await app.ainvoke(initial_state, config=config)

    print("\n--- 최종 결과물 ---")
    print("".join(final_state['story_parts']))

if __name__ == "__main__":
    asyncio.run(main())