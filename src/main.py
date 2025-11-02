from dotenv import load_dotenv
from graph import build_graph
from agents import GraphState

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()

# --- 5. 그래프 실행 ---
def main():
    app = build_graph()

    # 그래프 시각화 (선택 사항)
    try:
        img_data = app.get_graph().draw_mermaid_png()
        with open("graph.png", "wb") as f:
            f.write(img_data)
        print("그래프 이미지가 'graph.png'로 저장되었습니다.")
    except Exception as e:
        print(f"그래프 시각화 실패: {e}")


    # 그래프 실행
    initial_prompt = input("이야기의 시작 문장을 입력하세요: ")
    initial_state: GraphState = {"story_parts": [initial_prompt]}
    final_state = app.invoke(initial_state)

    print("\n--- 최종 결과물 ---")
    print("".join(final_state['story_parts']))

if __name__ == "__main__":
    main()