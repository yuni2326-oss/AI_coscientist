from unittest.mock import MagicMock
from agents.critic import CriticAgent
from models.schemas import Idea, ResearchInput

def test_critic_adds_scores():
    agent = CriticAgent()
    agent.runner = MagicMock()
    agent.runner.generate.return_value = """
    기술성숙도: 4
    실현가능성: 3
    독창성: 5
    제약조건충족: 4
    """
    idea = Idea(title="테스트", description="설명", approach="접근")
    research_input = ResearchInput(
        domain="센서", objective="목표", constraints=["저전력"]
    )
    scored = agent.score(idea, research_input)
    assert "기술성숙도" in scored.scores
    assert 1 <= scored.scores["기술성숙도"] <= 5
