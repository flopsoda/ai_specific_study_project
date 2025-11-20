from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from shared import global_state

app = FastAPI()

# 다크 테마가 적용된 HTML/CSS/JS
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
                max-width: 1400px; 
                margin: 0 auto; 
                padding: 20px; 
                background-color: var(--bg-color); 
                color: var(--text-main);
                height: 100vh;
                box-sizing: border-box;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }
            
            /* 스크롤바 커스텀 */
            ::-webkit-scrollbar { width: 10px; }
            ::-webkit-scrollbar-track { background: var(--bg-color); }
            ::-webkit-scrollbar-thumb { background: #585b70; border-radius: 5px; }
            ::-webkit-scrollbar-thumb:hover { background: #6c7086; }

            /* 상단 상태 바 */
            #status-bar {
                background: var(--panel-bg); 
                padding: 15px 25px; 
                border-radius: 12px;
                border: 1px solid var(--border-color);
                display: flex; 
                align-items: center; 
                gap: 15px;
                font-weight: bold; 
                color: var(--text-main); 
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
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

            /* 메인 레이아웃 */
            .container { display: flex; gap: 20px; flex: 1; overflow: hidden; }
            
            .box { 
                flex: 1; 
                background: var(--panel-bg); 
                padding: 20px; 
                border-radius: 16px; 
                border: 1px solid var(--border-color);
                display: flex; 
                flex-direction: column; 
                box-shadow: 0 10px 20px rgba(0,0,0,0.3);
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
                font-family: 'Ridibatang', 'KoPub Batang', serif; /* 가독성 좋은 명조 계열 권장 */
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

            /* 컨트롤 패널 (플로팅) */
            #control-panel {
                position: fixed; bottom: 40px; left: 50%; transform: translateX(-50%);
                background: rgba(30, 30, 46, 0.95);
                padding: 20px 40px; 
                border-radius: 50px;
                border: 1px solid var(--accent-color);
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                display: none; 
                gap: 20px; 
                align-items: center; 
                z-index: 100;
                backdrop-filter: blur(10px);
            }
            
            .btn { 
                padding: 12px 30px; 
                border: none; 
                border-radius: 25px; 
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
            
            .status-text { font-weight: bold; color: var(--text-muted); }
        </style>
    </head>
    <body>
        <!-- [추가] 상단 상태 바 -->
        <div id="status-bar">
            <div class="status-indicator"></div>
            <span id="status-text">시스템 초기화 중...</span>
        </div>

        <div class="container">
            <div class="box">
                <h2>📖 이야기 진행 상황</h2>
                <div id="story-container" class="content story-text"></div>
            </div>
            <div class="box">
                <h2>💬 캐릭터 토론 로그</h2>
                <div id="discussion-container" class="content"></div>
            </div>
        </div>

        <!-- 컨트롤 패널 -->
        <div id="control-panel">
            <span class="status-text">다음 행동을 선택하세요:</span>
            <button class="btn btn-continue" onclick="sendDecision('continue')">계속 진행 (Continue)</button>
            <button class="btn btn-end" onclick="sendDecision('end')">종료 (End)</button>
        </div>

        <script>
            async function updateData() {
                try {
                    const response = await fetch('/data');
                    const data = await response.json();
                    
                    // [추가] 상태 텍스트 업데이트
                    if (data.current_status) {
                        document.getElementById('status-text').innerText = data.current_status;
                    }

                    // 이야기 업데이트
                    const storyHtml = data.story_parts.join("\\n\\n");
                    document.getElementById('story-container').innerText = storyHtml;

                    // 토론 업데이트
                    const discussionContainer = document.getElementById('discussion-container');
                    discussionContainer.innerHTML = data.discussion.map(d => 
                        `<div class="item discussion-item">${d}</div>`
                    ).join('');
                    
                    // 스크롤 자동 내리기 (새로운 내용이 있을 때만)
                    // discussionContainer.scrollTop = discussionContainer.scrollHeight;

                    // 버튼 표시 여부 제어
                    const panel = document.getElementById('control-panel');
                    const indicator = document.querySelector('.status-indicator');
                    
                    if (data.waiting_for_input) {
                        panel.style.display = 'flex';
                        indicator.style.backgroundColor = '#f1c40f'; // 대기 중일 때는 노란색
                        indicator.style.animation = 'none'; // 애니메이션 멈춤
                    } else {
                        panel.style.display = 'none';
                        indicator.style.backgroundColor = '#2ecc71'; // 작동 중일 때는 초록색
                        indicator.style.animation = 'pulse 2s infinite'; // 애니메이션 재생
                    }
                    
                } catch (e) {
                    console.error("데이터 로드 실패", e);
                }
            }

            async function sendDecision(decision) {
                await fetch(`/decision/${decision}`, { method: 'POST' });
                // 클릭 후 즉시 패널 숨김 (반응성 향상)
                document.getElementById('control-panel').style.display = 'none';
                document.getElementById('status-text').innerText = "명령 전달 중...";
            }

            // 0.5초마다 데이터 갱신
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
    """웹에서 버튼을 누르면 이 API가 호출됩니다."""
    if decision in ["continue", "end"]:
        global_state["user_decision"] = decision
        return {"status": "ok", "decision": decision}
    return {"status": "error"}

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")