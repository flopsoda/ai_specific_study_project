# 콘솔과 웹 서버가 공유하는 상태 저장소
global_state = {
    "story_parts": [],
    "discussion": [],
    "waiting_for_input": False, 
    "user_decision": None,      
    "user_instruction": None,
    "current_status": "시스템 대기 중...",
    "phase": "ideation",
    "draft": None,
    "revision_count": 0,
    "current_node": None,  
}