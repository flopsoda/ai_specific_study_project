# 콘솔과 웹 서버가 공유하는 상태 저장소
global_state = {
    "story_parts": [],
    "discussion": [],
    "waiting_for_input": False, # 웹에서 입력을 기다리는 중인지 여부
    "user_decision": None       # 유저의 선택 ('continue' 또는 'end')
}