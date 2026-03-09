from core.ollama_runner import OllamaRunner
from models.schemas import Idea, ResearchInput
import re

SCORE_KEYS = ["기술성숙도", "실현가능성", "독창성", "제약조건충족"]

class CriticAgent:
    def __init__(self):
        self.runner = OllamaRunner()

    def score(self, idea: Idea, research_input: ResearchInput) -> Idea:
        prompt = f"""
다음 공학 연구 아이디어를 평가하세요 (각 항목 1~5점):

아이디어: {idea.title}
설명: {idea.description}
접근법: {idea.approach}
제약조건: {', '.join(research_input.constraints)}

각 항목을 다음 형식으로 점수만 작성하세요:
기술성숙도: [1-5]
실현가능성: [1-5]
독창성: [1-5]
제약조건충족: [1-5]
"""
        raw = self.runner.generate(prompt)
        idea.scores = self._parse_scores(raw)
        return idea

    def score_all(self, ideas: list[Idea], research_input: ResearchInput) -> list[Idea]:
        return [self.score(idea, research_input) for idea in ideas]

    def _parse_scores(self, raw: str) -> dict[str, int]:
        scores = {}
        for key in SCORE_KEYS:
            match = re.search(rf"{key}[:\s]+([1-5])", raw)
            scores[key] = int(match.group(1)) if match else 3
        return scores
