from core.ollama_runner import OllamaRunner
from models.schemas import ResearchInput, Idea
from config import settings
import re

SYSTEM_PROMPT = """당신은 공학 연구 아이디어 생성 전문가입니다.
센서, 광학 시스템, 회로 설계 분야에 깊은 지식을 가지고 있습니다.
주어진 연구 목표와 제약조건에 맞는 창의적이고 실현 가능한 아이디어를 생성하세요."""

class GeneratorAgent:
    def __init__(self):
        self.runner = OllamaRunner()

    def generate(self, research_input: ResearchInput) -> list[Idea]:
        prompt = f"""
다음 연구 목표에 대해 {settings.max_ideas}가지 서로 다른 공학적 접근 아이디어를 생성하세요.

도메인: {research_input.domain}
목표: {research_input.objective}
제약조건: {', '.join(research_input.constraints)}
배경정보: {research_input.background or '없음'}

각 아이디어를 다음 형식으로 작성하세요:
아이디어 N: [제목]
설명: [구체적인 설명]
접근법: [기술적 접근 방법]
---
"""
        raw = self.runner.generate(prompt, system=SYSTEM_PROMPT)
        return self._parse_ideas(raw)

    def _parse_ideas(self, raw: str) -> list[Idea]:
        ideas = []
        blocks = raw.split("---")
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            title_match = re.search(r"아이디어\s*\d+[:\.]?\s*(.+)", block)
            desc_match = re.search(r"설명[:\s]+(.+?)(?=접근법|$)", block, re.DOTALL)
            approach_match = re.search(r"접근법[:\s]+(.+?)$", block, re.DOTALL)
            if title_match:
                ideas.append(Idea(
                    title=title_match.group(1).strip(),
                    description=desc_match.group(1).strip() if desc_match else "",
                    approach=approach_match.group(1).strip() if approach_match else ""
                ))
        return ideas if ideas else [Idea(title="생성된 아이디어", description=raw[:200], approach="")]
