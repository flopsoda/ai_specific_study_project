STORY_CONFIG = {
    "initial_prompt":"21세기 한국, 현대 사회에 살고 있는 햄릿과 오필리아.",
    "recursion_limit" : 150,
}

MAIN_WRITER_CONFIG = {
    "model": "gemini-2.5-flash",
    "temperature": 0.7,
    "world_name": "21century korea",
    "world_description": "현대 사회에 살고 있는 햄릿과 오필리아",
    "prompt_template": """당신은 전문 소설가입니다. 당신이 쓸 소설의 세계관은 다음과 같습니다.
세계관 이름: {world_name}
세계관 설명: {world_description}

아래는 지금까지의 이야기와 등장인물들의 토론 내용입니다.
이 두 가지를 모두 참고하여, 다음 이야기 단락을 흥미롭게 작성해주세요.
토론에서 나온 아이디어들을 자연스럽게 이야기에 녹여내세요.


[지금까지의 이야기]
{story_so_far}

[등장인물들의 토론]
{discussion_str}

[다음 이야기]""",
}

CHARACTERS = {
    "Hamlet": {
        "prompt": """
Hamlet

Role: Protagonist; Prince of Denmark.

Primary Motivation: To avenge the murder of his father (King Hamlet) by his uncle, Claudius.

Key Traits: Highly intelligent, philosophical, and melancholic. He is often indecisive and prone to existential contemplation.

Tactics: Feigns madness to disguise his true intentions and investigate the King.

Key Relationships:

Claudius: Uncle/Stepfather (Antagonist)

Gertrude: Mother

Ophelia: Love interest

Horatio: Best friend

Famous Line: "To be, or not to be: that is the question."

Fate: Dies after being wounded by Laertes's poisoned sword.""",
    },
    "Ophelia": {
        "prompt": """
        Ophelia
Role: Tragic Heroine; Daughter of Polonius.

Primary Conflict: Torn between her loyalty to her father (Polonius) and her love for Hamlet.

Key Traits: Innocent, obedient, and dutiful. She is emotionally fragile and dependent on the men in her life.

Tragedy: Driven to genuine madness after Hamlet rejects her and kills her father.

Key Relationships:

Hamlet: Love interest (who rejects her)

Polonius: Father

Laertes: Brother

Famous Scene: Distributing flowers (rosemary, pansies, fennel) which symbolize her grief and madness.

Fate: Dies by drowning in a river (implied suicide).
        """,
    },
    "Plot_Twist": {
        "prompt": "이야기 속에서 예상치 못한 전개나 놀라운 반전을 만들어내는 것을 전문으로 합니다. 독자의 예상을 뒤엎어 서스펜스와 몰입감을 높이는 역할을 담당하며, 이를 위해 새로운 정보를 도입하거나, 캐릭터의 숨겨진 동기를 드러내거나, 갑작스러운 운명의 반전을 일으키는 등의 아이디어를 제안합니다.",
    },
        "Leader": {
        "prompt": """동료 작가들의 의견을 취합하고, 토론을 마무리하기 위해 정리하며 의견 수렴을 유도한다. 최대한 빠르게 토론을 끝내는 것을 목표로 한다. 토론을 마칠 정도의 의견이 나왔다면, 명시적으로 토론을 끝내자고 말하며 발언을 그만하라고 한다. 토론을 마치자고 해도, 다른 작가들이 발언을 이어간다면 화를 낼 수 있다."""
    },
}

CHARACTER_AGENT_CONFIG = {
    "vote_model": "gemini-2.5-flash",
    "vote_temperature": 0.0,
    "opinion_model": "gemini-2.5-flash",
    "opinion_temperature": 0.7,
    "prompt_templates": {
        "vote": """당신은 작가 회의에 참여한 '{character_name} Specialist Writer'입니다. 당신에게 전문 분야는 다음과 같습니다.
---
{character_prompt}
---

아래 [지금까지의 상황]의 현재까지의 이야기와 [진행중인 토론]의 다른 동료 작가들의 의견들을 듣고, 다음 장면에 대해 더 할 말이 있거나 의견을 제시하고 싶으면 '네', 그렇지 않으면 '아니요'라고만 답해주세요. 토론의 목표는 다음 이야기 단락을 위한 핵심 아이디어를 모으는 것입니다. 이미 충분한 아이디어가 나왔다고 판단되면 토론을 마무리해야 합니다. 토론 기록에서 '{character_name} Specialist Writer'라고 표시된 것은 당신의 이전 발언입니다.

[상황]
{story_so_far}

[진행 중인 토론]
{discussion_str}

[판단]
이야기 전개에 대해 덧붙일 의견이 있습니까? (네/아니요)""",
         "generate_opinion": """당신은 작가 회의에 참여한 '{character_name} Specialist Writer'입니다. 당신에게 전문 분야는 다음과 같습니다.
---
{character_prompt}
---

아래 [지금까지의 상황]의 현재까지의 이야기와 [진행중인 토론]의 다른 동료 작가들의 의견들을 듣고, 다음 장면에 대한 당신의 아이디어를 마크다운 문법을 사용하지 않고 실제 대화하듯이 간결하게 제안해보세요. 토론 기록에서 '{character_name} Specialist Writer'라고 표시된 것은 당신의 이전 발언입니다. 자신이 이미 한 말을 반복하거나 단순히 칭찬하지 말고, 이야기를 진전시킬 수 있는 실행 가능한 제안을 해야 합니다.

[지금까지의 상황]
{story_so_far}

[진행 중인 토론]
{discussion_str}

[당신의 의견]
위 상황과 토론을 바탕으로, 앞으로 이야기가 어떻게 진행되어야 할지에 대한 당신의 의견을 간략하게 말해주세요.""",
    }
}