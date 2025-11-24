from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from shared import global_state
import os

app = FastAPI()

# 데이터 수신용 모델 정의
class DecisionRequest(BaseModel):
    decision: str
    instruction: str = ""

# 템플릿 파일 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

@app.get("/", response_class=HTMLResponse)
async def get_ui():
    # templates 폴더의 index.html 파일을 반환합니다.
    return FileResponse(os.path.join(TEMPLATES_DIR, "index.html"))

@app.get("/data")
async def get_data():
    return global_state

@app.post("/decision")
async def set_decision(req: DecisionRequest):
    """웹에서 버튼을 누르면 이 API가 호출됩니다."""
    if req.decision in ["continue", "end"]:
        global_state["user_decision"] = req.decision
        global_state["user_instruction"] = req.instruction # [추가] 사용자 입력 저장
        return {"status": "ok"}
    return {"status": "error"}

def start_server():
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="error")