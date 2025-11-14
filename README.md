# AI 협업 소설 생성기 (AI Collaborative Story Generator)

이 프로젝트는 LangGraph와 Google Gemini API를 사용하여 여러 AI 에이전트가 협력하여 소설을 창작하는 시스템입니다. 각 에이전트는 특정 캐릭터나 역할을 맡아 토론을 통해 아이디어를 내고, 메인 작가 에이전트가 이 토론을 바탕으로 다음 이야기 단락을 작성합니다.

## 주요 기능

-   **다중 에이전트 시스템**: 각기 다른 개성과 역할을 가진 AI 에이전트들이 작가 회의처럼 토론에 참여합니다.
-   **동적 토론 과정**: 에이전트들은 이야기의 흐름에 따라 발언권을 얻기 위해 경쟁하고, 토론이 충분히 무르익으면 다음 이야기 생성으로 넘어갑니다.
-   **LangGraph 기반 제어 흐름**: 에이전트 간의 상호작용과 상태 관리를 LangGraph를 사용하여 체계적으로 구현했습니다.
-   **쉬운 커스터마이징**: `src/config.py` 파일을 수정하여 초기 프롬프트, 세계관, 등장 캐릭터의 성격과 역할을 쉽게 변경할 수 있습니다.

## 프로젝트 구조

```
.
├── .env.example        # 환경 변수 예시 파일
├── .gitignore          # Git 추적 제외 목록
├── requirements.txt    # 프로젝트 의존성 목록
├── src/
│   ├── agents.py       # 각 에이전트(노드)의 로직 정의
│   ├── config.py       # 프롬프트, 캐릭터, 모델 설정
│   ├── graph.py        # LangGraph의 전체 구조(워크플로우) 정의
│   └── main.py         # 프로그램 실행 진입점
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

프로그램이 실행되면, 콘솔에 이야기의 첫 부분이 출력되고 계속 진행할지 묻는 메시지가 나타납니다. `c`를 입력하면 AI 에이전트들의 토론이 시작되고, 토론이 끝나면 다음 이야기 단락이 생성됩니다. `e`를 입력하면 프로그램이 종료됩니다.

## 커스터마이징

`src/config.py` 파일을 수정하여 자신만의 이야기를 만들 수 있습니다.

-   `STORY_CONFIG["initial_prompt"]`: 이야기의 시작 부분을 변경합니다.
-   `MAIN_WRITER_CONFIG`: 소설의 전체적인 세계관(`world_name`, `world_description`)을 설정합니다.
-   `CHARACTERS`: 토론에 참여할 캐릭터(에이전트)들의 이름, 역할, 성격 등을 자유롭게 추가하거나 수정할 수 있습니다.