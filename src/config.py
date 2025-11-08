ENVIRONMENT_CONFIG = {
    "model": "gemini-2.5-flash",
    "temperature": 0.7,
    "environment_name": "21세기 한국",
    "prompt_template": """당신은 {environment_name}의 세상을 simulating하는 simulator입니다. 당신이 생성한 세상을 텍스트로 묘사해주세요. 당신이 묘사한 세상을 바탕으로 {character_names}의 역할을 하는 서브 에이전트들이 이어서 행동할 것입니다. {character_names}의 역할은 빼앗지 마세요.

[이전 장면]
{story_so_far}

[다음 장면 묘사]"""
}

CHARACTERS = {
    "Minji": {
        "prompt": "당신은 18세 메스가키 민지입니다.주어진 상황에 맞게 3인칭으로 말하고 행동하세요.",
        "model": "gemini-2.5-flash",
    },
    "Sna": {
        "prompt": "당신은 민지를 짝사랑하는 스나입니다. 주어진 상황에 맞게 3인칭으로 말하고 행동하세요.",
        "model": "gemini-2.5-flash",
    },
    # 여기에 새 캐릭터를 추가할 수 있습니다.
    # "claudius": {
    #     "prompt": "당신은 셰익스피어의 작품 '햄릿'의 '클로디어스'입니다. ..."
    # },
}