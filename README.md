# AI 협업 소설 생성기 (AI Collaborative Story Generator)

이 프로젝트는 LangGraph와 Google Gemini API를 사용하여 여러 AI 에이전트가 협력하여 소설을 창작하는 시스템입니다. 
단순한 텍스트 생성을 넘어, **RAG(검색 증강 생성) 기반의 장기 기억**과 **실시간 웹 대시보드**를 통해 에이전트들의 사고 과정과 집필 현황을 시각적으로 확인할 수 있습니다.

## 주요 기능

-   **다중 에이전트 협업**:각기 다른 페르소나를 가진 AI 작가들이 회의를 통해 아이디어를 냅니다.
-   **실시간 웹 대시보드 (Dark Theme)**:
    -   **상태 모니터링**: 현재 누가 발언권을 얻으려 하는지, 메인 작가가 집필 중인지 실시간으로 확인합니다.
    -   **속마음 시각화**: 캐릭터들이 왜 그런 발언을 하려는지(혹은 침묵하는지) 내면의 판단 과정을 카드 형태로 보여줍니다.
    -   **사용자 개입**: 웹 UI에서 '계속 진행' 또는 '종료'를 제어할 수 있습니다.
-   **RAG 기반 장기 기억 (LoreBook)**:
    -   이야기가 길어지면 오래된 내용을 자동으로 요약하여 벡터 DB(FAISS)에 저장합니다.
    -   새로운 내용을 쓸 때 과거의 설정이나 사건을 검색(Retrieval)하여 반영하므로, 설정 붕괴 없는 장기 연재가 가능합니다.
-   **LangGraph 제어 흐름**: 에이전트 간의 발언권 경쟁, 토론, 집필, 기억 검색 등의 복잡한 흐름을 그래프로 제어합니다.

## 프로젝트 구조

```
.
├── .env.example        # 환경 변수 예시 파일
├── .gitignore          # Git 추적 제외 목록
├── requirements.txt    # 프로젝트 의존성 목록
├── src/
│   ├── agents.py       # 각 에이전트(노드)의 로직 및 프롬프트 처리
│   ├── config.py       # 캐릭터 설정, 세계관, LLM 모델 설정
│   ├── graph.py        # LangGraph 워크플로우(노드/엣지) 정의
│   ├── main.py         # 프로그램 실행 진입점 (서버 및 그래프 시작)
│   ├── memory.py       # RAG 시스템 (FAISS 벡터 DB 및 요약 관리)
│   ├── server.py       # FastAPI 기반 웹 대시보드 서버
│   ├── shared.py       # 스레드 간 상태 공유를 위한 전역 변수
│   └── utils.py        # 텍스트 처리 및 유틸리티 함수
└── README.md           # 프로젝트 설명 파일
```

## 설치 및 설정

1.  **저장소 복제**
    ```bash
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **가상 환경 생성 및 활성화 (권장)**
    ```bash
    python -m venv venv
    # Windows
    venv\Scripts\activate
    # macOS/Linux
    source venv/bin/activate
    ```

3.  **의존성 패키지 설치**
    ```bash
    pip install -r requirements.txt
    ```

4.  **환경 변수 설정**
    `.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.
    ```bash
    # Windows
    copy .env.example .env
    # macOS/Linux
    cp .env.example .env
    ```
    그 다음, 생성된 `.env` 파일을 열어 `your_api_key_here` 부분에 자신의 Google API 키를 입력합니다.
    ```
    GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
    ```

## 실행 방법

프로젝트를 실행하려면 다음 명령어를 터미널에 입력하세요.

```bash
python src/main.py
```

1.  터미널에 실행 로그가 출력됩니다.
2.  웹 브라우저를 열고 **`http://127.0.0.1:8000`** 에 접속합니다.
3.  대시보드에서 실시간으로 생성되는 이야기와 캐릭터들의 토론, 속마음을 관전합니다.
4.  우측 하단의 컨트롤 패널을 통해 진행 여부를 결정합니다.

## 커스터마이징

`src/config.py` 파일을 수정하여 자신만의 이야기를 만들 수 있습니다.

-   `STORY_CONFIG["initial_prompt"]`: 이야기의 도입부를 수정합니다.
-   `MAIN_WRITER_CONFIG`: 소설의 세계관(World View)을 설정합니다.
-   `CHARACTERS`: 참여할 캐릭터 에이전트들의 성격, 말투, 역할을 정의합니다.