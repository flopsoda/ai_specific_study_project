# AI 협업 소설 생성기 (AI Collaborative Story Generator)

LangGraph와 Google Gemini API를 활용한 **멀티 에이전트 협업 소설 창작 시스템**입니다.

여러 AI 에이전트가 회의를 통해 아이디어를 제안하고, 초안을 작성하고, 서로 비평하며 수정하는 **반복적 개선(Iterative Refinement)** 과정을 거쳐 소설을 완성합니다.

## ✨ 주요 기능

### 🤖 다중 에이전트 협업
- 각기 다른 역할(총괄 진행, 시리즈 구성, 캐릭터 담당)을 가진 AI 작가들이 회의를 통해 아이디어를 냅니다.
- **1차 회의(Ideation)**: 다음 장면에 대한 아이디어 제안
- **비평 회의(Critique)**: 초안에 대한 문제점 지적 및 수정 요청

### 🔄 반복적 개선 시스템
- 메인 작가가 초안을 작성하면, 다른 작가들이 비평합니다.
- 편집장(Judge)이 비평 내용을 검토하여 통과/수정 여부를 결정합니다.
- 수정이 필요하면 다시 작가에게 돌아가 반복됩니다. (최대 3회)

### 🧠 RAG 기반 장기 기억 (LoreBook)
- 이야기가 길어지면 오래된 내용을 자동으로 벡터 DB(FAISS)에 저장합니다.
- 새로운 내용을 쓸 때 과거의 설정이나 사건을 검색(Retrieval)하여 반영합니다.
- 설정 붕괴 없는 장기 연재가 가능합니다.

### 🖥️ 실시간 웹 대시보드
- **상태 모니터링**: 현재 어떤 노드가 실행 중인지 실시간으로 확인
- **워크플로우 시각화**: 상단의 미니 그래프로 현재 진행 상황 파악
- **초안 표시**: 작성 중인 초안과 수정 횟수 실시간 확인
- **사용자 개입**: '계속 진행' 또는 '종료' 제어, 직접 상황 개입 가능

## 📁 프로젝트 구조

```
.
├── .env.example        # 환경 변수 예시 파일
├── .gitignore          # Git 추적 제외 목록
├── requirements.txt    # 프로젝트 의존성 목록
├── README.md           # 프로젝트 설명 파일
└── src/
    ├── main.py         # 프로그램 실행 진입점
    ├── graph.py        # LangGraph 워크플로우 정의
    ├── agents.py       # 각 에이전트(노드) 로직
    ├── config.py       # 캐릭터, 세계관, LLM 설정
    ├── memory.py       # RAG 시스템 (FAISS 벡터 DB)
    ├── server.py       # FastAPI 웹 서버
    ├── shared.py       # 스레드 간 상태 공유
    ├── utils.py        # 유틸리티 함수
    └── templates/
        └── index.html  # 웹 대시보드 UI
```

## 🚀 설치 및 실행

### 1. 저장소 복제
```bash
git clone <your-repository-url>
cd <your-repository-name>
```

### 2. 가상 환경 생성 및 활성화
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. 의존성 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
# Windows
copy .env.example .env

# macOS/Linux
cp .env.example .env
```

`.env` 파일을 열어 Google API 키를 입력합니다:
```
GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"
```

### 5. 실행
```bash
python src/main.py
```

웹 브라우저에서 **http://127.0.0.1:8000** 에 접속하여 대시보드를 확인합니다.

## ⚙️ 커스터마이징

`src/config.py` 파일을 수정하여 자신만의 이야기를 만들 수 있습니다.

| 설정 | 설명 |
|------|------|
| `STORY_CONFIG["initial_prompt"]` | 이야기의 도입부 |
| `MAIN_WRITER_CONFIG` | 세계관 이름, 설명, LLM 모델 설정 |
| `CHARACTERS` | 참여할 캐릭터 에이전트들의 역할과 성격 |

## 🔧 기술 스택

- **LangGraph**: 에이전트 워크플로우 관리
- **LangChain**: LLM 통합 및 프롬프트 관리
- **Google Gemini API**: 텍스트 생성
- **FAISS**: 벡터 유사도 검색 (RAG)
- **FastAPI**: 웹 서버
- **HTML/CSS/JS**: 실시간 대시보드 UI