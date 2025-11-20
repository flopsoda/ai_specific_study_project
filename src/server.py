from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from shared import global_state

app = FastAPI()

# 다크 테마가 적용된 HTML/CSS/JS (2열 레이아웃 적용)
html_content = """
<!DOCTYPE html>
<html>
    <head>
        <title>AI 소설 생성 모니터링</title>
        <meta charset="utf-8">
        <style>
            :root {
                --bg-color: #1e1e2e;
                --panel-bg: #313244;
                --text-main: #cdd6f4;
                --text-muted: #a6adc8;
                --accent-color: #89b4fa;
                --border-color: #45475a;
                --success-color: #a6e3a1;
                --danger-color: #f38ba8;
                --warning-color: #f9e2af;
            }

            body { 
                font-family: 'Pretendard', 'Segoe UI', sans-serif; 
                margin: 0; 
                padding: 20px; 
                background-color: var(--bg-color); 
                color: var(--text-main);
                height: 100vh;
                box-sizing: border-box;
                overflow: hidden; /* 전체 스크롤 방지 */
            }
            
            /* 스크롤바 커스텀 */
            ::-webkit-scrollbar { width: 8px; }
            ::-webkit-scrollbar-track { background: transparent; }
            ::-webkit-scrollbar-thumb { background: #585b70; border-radius: 4px; }
            ::-webkit-scrollbar-thumb:hover { background: #6c7086; }

            /* 메인 레이아웃: 2열 구조 */
            .main-layout {
                display: flex;
                gap: 20px;
                height: 100%;
                width: 100%;
            }

            .col-left, .col-right {
                display: flex;
                flex-direction: column;
                gap: 20px;
                flex: 1;
                min-width: 0; /* Flex 자식 넘침 방지 */
            }

            /* --- 왼쪽 열 스타일 --- */

            /* 상태 바 (이제 왼쪽 열 상단에 위치) */
            #status-bar {
                background: var(--panel-bg); 
                padding: 15px 20px; 
                border-radius: 12px;
                border: 1px solid var(--border-color);
                display: flex; 
                align-items: center; 
                gap: 15px;
                font-weight: bold; 
                color: var(--text-main); 
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                flex-shrink: 0; /* 크기 줄어들지 않음 */
            }
            .status-indicator {
                width: 12px; height: 12px; 
                background-color: var(--success-color); 
                border-radius: 50%;
                box-shadow: 0 0 10px var(--success-color);
                transition: all 0.3s ease;
            }
            .status-pulse { animation: pulse 2s infinite; }
            
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(166, 227, 161, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(166, 227, 161, 0); }
                100% { box-shadow: 0 0 0 0 rgba(166, 227, 161, 0); }
            }

            /* 박스 공통 스타일 */
            .box { 
                background: var(--panel-bg); 
                padding: 20px; 
                border-radius: 16px; 
                border: 1px solid var(--border-color);
                display: flex; 
                flex-direction: column; 
                box-shadow: 0 10px 20px rgba(0,0,0,0.3);
                flex: 1; /* 남은 공간 모두 차지 */
                overflow: hidden; /* 내부 스크롤을 위해 필수 */
            }
            
            h2 { 
                margin-top: 0; 
                padding-bottom: 15px; 
                border-bottom: 1px solid var(--border-color); 
                color: var(--accent-color); 
                font-size: 1.2rem;
                display: flex;
                align-items: center;
                gap: 10px;
                flex-shrink: 0;
            }

            .content { 
                flex: 1; 
                overflow-y: auto; 
                padding-right: 10px; 
                font-size: 1.05rem;
            }

            /* 이야기 텍스트 스타일 */
            .story-text { 
                white-space: pre-wrap; 
                line-height: 1.8; 
                color: var(--text-main); 
                font-family: 'Ridibatang', 'KoPub Batang', serif; 
            }
            .story-paragraph { margin-bottom: 1.5em; text-align: justify; }

            /* 토론 로그 스타일 */
            .discussion-item { 
                margin-bottom: 12px; 
                padding: 15px; 
                background: #45475a; 
                border-radius: 12px; 
                border-left: 4px solid var(--accent-color); 
                line-height: 1.6;
                color: #eceff4;
            }
            .discussion-item strong { color: var(--accent-color); }

            /* --- 오른쪽 열 스타일 --- */

            /* 컨트롤 패널 (이제 오른쪽 열 하단에 고정) */
            #control-panel {
                background: rgba(30, 30, 46, 0.5);
                padding: 20px; 
                border-radius: 16px;
                border: 1px solid var(--accent-color);
                /* display: flex; -> JS에서 제어 */
                display: none;
                flex-direction: column;
                gap: 15px; 
                align-items: center; 
                justify-content: center;
                flex-shrink: 0; /* 크기 줄어들지 않음 */
                margin-top: auto; /* 위쪽 요소 밀어내기 */
            }
            
            .btn-group {
                display: flex;
                gap: 15px;
                width: 100%;
            }

            .btn { 
                flex: 1;
                padding: 15px; 
                border: none; 
                border-radius: 12px; 
                font-size: 16px; 
                font-weight: bold; 
                cursor: pointer; 
                transition: all 0.2s; 
                color: #1e1e2e;
            }
            .btn:hover { transform: translateY(-2px); filter: brightness(1.1); }
            .btn:active { transform: scale(0.95); }
            
            .btn-continue { background: var(--success-color); }
            .btn-end { background: var(--danger-color); }
            
            .status-text-prompt { font-weight: bold; color: var(--text-main); }

        </style>
    </head>
    <body>
        <div class="main-layout">
            <!-- [왼쪽 열] 상태 바 + 이야기 -->
            <div class="col-left">
                <div id="status-bar">
                    <div class="status-indicator status-pulse"></div>
                    <span id="status-text">시스템 초기화 중...</span>
                </div>
                
                <div class="box">
                    <h2>📖 이야기 (Story)</h2>
                    <div id="story-container" class="content story-text"></div>
                </div>
            </div>

            <!-- [오른쪽 열] 토론 + 컨트롤 패널 -->
            <div class="col-right">
                <div class="box">
                    <h2>💬 작가 회의 (Discussion)</h2>
                    <div id="discussion-container" class="content"></div>
                </div>

                <!-- 컨트롤 패널 (평소엔 숨겨져 있다가 필요할 때 나타남) -->
                <div id="control-panel">
                    <span class="status-text-prompt">다음 행동을 선택하세요:</span>
                    <div class="btn-group">
                        <button class="btn btn-continue" onclick="sendDecision('continue')">계속 진행</button>
                        <button class="btn btn-end" onclick="sendDecision('end')">종료</button>
                    </div>
                </div>
            </div>
        </div>

        <script>
            let lastDiscussionLength = 0;
            let lastStoryLength = 0;

            async function updateData() {
                try {
                    const response = await fetch('/data');
                    const data = await response.json();
                    
                    // 상태 텍스트 업데이트
                    if (data.current_status) {
                        document.getElementById('status-text').innerText = data.current_status;
                    }

                    // 이야기 업데이트
                    if (data.story_parts.length !== lastStoryLength) {
                        const storyHtml = data.story_parts.map(part => `<div class="story-paragraph">${part}</div>`).join("");
                        const storyContainer = document.getElementById('story-container');
                        storyContainer.innerHTML = storyHtml;
                        storyContainer.scrollTop = storyContainer.scrollHeight;
                        lastStoryLength = data.story_parts.length;
                    }

                    // 토론 업데이트
                    if (data.discussion.length !== lastDiscussionLength) {
                        const discussionContainer = document.getElementById('discussion-container');
                        discussionContainer.innerHTML = data.discussion.map(d => {
                            const formatted = d.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
                            return `<div class="discussion-item">${formatted}</div>`;
                        }).join('');
                        discussionContainer.scrollTop = discussionContainer.scrollHeight;
                        lastDiscussionLength = data.discussion.length;
                    }

                    // 버튼 표시 제어
                    const panel = document.getElementById('control-panel');
                    const indicator = document.querySelector('.status-indicator');
                    
                    if (data.waiting_for_input) {
                        panel.style.display = 'flex'; // 패널 보이기
                        indicator.style.backgroundColor = '#f9e2af';
                        indicator.style.boxShadow = '0 0 10px #f9e2af';
                        indicator.classList.remove('status-pulse');
                    } else {
                        panel.style.display = 'none'; // 패널 숨기기 (토론창이 자동으로 늘어남)
                        indicator.style.backgroundColor = '#a6e3a1';
                        indicator.style.boxShadow = '0 0 10px #a6e3a1';
                        indicator.classList.add('status-pulse');
                    }
                    
                } catch (e) {
                    console.error("데이터 로드 실패", e);
                }
            }

            async function sendDecision(decision) {
                await fetch(`/decision/${decision}`, { method: 'POST' });
                // 즉시 UI 반영
                document.getElementById('control-panel').style.display = 'none';
                document.getElementById('status-text').innerText = "명령 전달 중...";
            }

            setInterval(updateData, 500);
            updateData();
        </script>
    </body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    return html_content

@app.get("/data")
async def get_data():
    return global_state

@app.post("/decision/{decision}")
async def set_decision(decision: str):
    if decision in ["continue", "end"]:
        global_state["user_decision"] = decision
        return {"status": "ok", "decision": decision}
    return {"status": "error"}

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")