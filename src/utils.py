from typing import List
from config import STORY_CONTEXT_WINDOW  # [추가] 설정값 임포트

def get_story_context(story_parts: List[str], window_size: int = STORY_CONTEXT_WINDOW) -> str:
    """
    전체 이야기 리스트에서 최근 N개의 문단만 추출하여 문자열로 반환합니다.
    토큰 제한을 방지하기 위해 사용됩니다.
    
    Args:
        story_parts: 전체 이야기 조각 리스트
        window_size: 가져올 최근 문단 개수 (기본값: config.py의 STORY_CONTEXT_WINDOW)
        
    Returns:
        str: 합쳐진 이야기 문자열
    """
    if not story_parts:
        return ""
        
    # 최근 window_size만큼만 슬라이싱
    recent_parts = story_parts[-window_size:]
    context = "".join(recent_parts)
    
    # 앞부분이 잘렸다면 표시 (선택 사항)
    if len(story_parts) > window_size:
        context = f"(...이전 {len(story_parts) - window_size}개의 문단 생략됨...)\n" + context
        
    return context