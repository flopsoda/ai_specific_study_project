from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import uvicorn
from shared import global_state

app = FastAPI()

html_content = """
<!DOCTYPE html>
<html>
    <head>
        <title>AI 소설 생성 모니터링</title>
        <meta charset="utf-8">
        <style>
            body { font-family: 'Segoe UI', sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px; display: flex; flex-direction: column; gap: 20px; background-color: #f0f2f5; }
            
            /* [추가] 상태 바 스타일 */
            #status-bar {
                background: white; padding: 15px 25px; border-radius: 12px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                display: flex; align-items: center; gap: 15px;
                font-weight: bold; color: #333; border-left: 5px solid #6c5ce7;
            }
            .status-indicator {
                width: 12px; height: 12px; background-color: #2ecc71; border-radius: 50%;
                box-shadow: 0 0 0 rgba(46, 204, 113, 0.4);
                animation: pulse 2s infinite;
            }
            @keyframes pulse {
                0% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0.7); }
                70% { box-shadow: 0 0 0 10px rgba(46, 204, 113, 0); }
                100% { box-shadow: 0 0 0 0 rgba(46, 204, 113, 0); }
            }

            .container { display: flex; gap: 20px; height: 75vh; }
            .box { flex: 1; background: white; padding: 20px; border-radius: 12px; overflow-y: auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
            h2 { margin-top: 0; padding-bottom: 15px; border-bottom: 2px solid #eee; color: #333; }
            .content { flex: 1; overflow-y: auto; }
            .item { margin-bottom: 12px; padding: 12px; background: #f8f9fa; border-radius: 8px; border-left: 4px solid #ddd; }
            .story-text { white-space: pre-wrap; line-height: 1.8; color: #2c3e50; }
            .discussion-item { border-left-color: #007bff; }
            
            /* 컨트롤 패널 스타일 */
            #control-panel {
                position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
                background: white; padding: 15px 30px; border-radius: 50px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.2);
                display: none; /* 기본적으로 숨김 */
                gap: 15px; align-items: center; z-index: 100;
            }
            .btn { padding: 12px 24px; border: none; border-radius: 25px; font-size: 16px; font-weight: bold; cursor: pointer; transition: transform 0.1s; }
            .btn:active { transform: scale(0.95); }
            .btn-continue { background: #28a745; color: white; }
            .btn-end { background: #dc3545; color: white; }
            .status-text { font-weight: bold; color: #555; }
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