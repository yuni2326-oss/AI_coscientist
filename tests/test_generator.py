from unittest.mock import MagicMock, patch
from agents.generator import GeneratorAgent
from models.schemas import ResearchInput, Idea

def make_input():
    return ResearchInput(
        domain="광학 센서",
        objective="저조도 환경 고감도 측정",
        constraints=["저전력", "소형화"]
    )

def test_generate_returns_ideas():
    agent = GeneratorAgent()
    agent.runner = MagicMock()
    agent.runner.generate.return_value = """
    아이디어 1: APD 기반 설계
    설명: 아발란체 포토다이오드를 활용한 고감도 수광부
    접근법: APD 바이어스 회로 최적화로 증폭률 향상
    ---
    아이디어 2: SPAD 어레이
    설명: 단일 광자 검출 어레이 구성
    접근법: 시간 상관 광자 계수법 적용
    """
    ideas = agent.generate(make_input())
    assert isinstance(ideas, list)
    assert len(ideas) >= 1
    assert isinstance(ideas[0], Idea)
