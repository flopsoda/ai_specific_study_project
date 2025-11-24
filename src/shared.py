# 콘솔과 웹 서버가 공유하는 상태 저장소
global_state = {
    "story_parts": [],
    "discussion": [],
    "waiting_for_input": False, 
    "user_decision": None,      
    "user_instruction": None,   # [추가] 사용자가 입력한 '신의 개입' 텍스트
    "current_status": "시스템 대기 중...",
    "character_thoughts": {}    
}