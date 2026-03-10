import re
from core.claude_runner import ClaudeRunner
from models.schemas import Idea, ResearchInput, ResearchProposal


class SynthesizerAgent:
    def __init__(self):
        self.claude = ClaudeRunner()

    def synthesize(self, research_input: ResearchInput, idea: Idea, references: list[str]) -> ResearchProposal:
        raw = self.claude.generate(self._build_prompt(research_input, idea))
        design_spec, experiment_plan, simulation = self._parse_sections(raw)

        return ResearchProposal(
            title=f"{research_input.domain} - {idea.title}",
            input=research_input,
            selected_idea=idea,
            design_spec=design_spec,
            experiment_plan=experiment_plan,
            simulation_suggestion=simulation,
            references=references
        )

    def _build_prompt(self, ri: ResearchInput, idea: Idea) -> str:
        return f"""다음 공학 연구 아이디어에 대해 연구 제안서의 3개 섹션을 한 번에 작성해주세요.

도메인: {ri.domain}
목표: {ri.objective}
제약조건: {', '.join(ri.constraints)}
선택된 접근법: {idea.title}
접근법 상세: {idea.approach}

아래 형식을 정확히 따라 작성하세요. 각 섹션 헤더(##)는 반드시 포함해야 합니다.

## 설계 사양
- 핵심 부품/재료 사양
- 성능 목표 수치
- 구조/회로 설명
- 예상 도전 과제

## 실험 계획
- 1단계: 기초 특성 검증
- 2단계: 성능 최적화 실험
- 3단계: 환경 내성 테스트
- 측정 장비 및 방법

## 시뮬레이션 방법
- 추천 시뮬레이션 도구 (SPICE, FDTD, FEM, Python 등)
- 핵심 시뮬레이션 파라미터
- 예시 Python 코드 스니펫 (있으면)
"""

    def _parse_sections(self, raw: str) -> tuple[str, str, str]:
        """## 헤더 기준으로 3개 섹션 파싱"""
        sections = {"설계 사양": "", "실험 계획": "", "시뮬레이션 방법": ""}
        pattern = re.compile(r"^##\s+(설계 사양|실험 계획|시뮬레이션 방법)", re.MULTILINE)
        matches = list(pattern.finditer(raw))

        for i, match in enumerate(matches):
            key = match.group(1)
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
            sections[key] = raw[start:end].strip()

        # 파싱 실패 시 전체 텍스트를 설계 사양에 담음
        if not any(sections.values()):
            sections["설계 사양"] = raw

        return sections["설계 사양"], sections["실험 계획"], sections["시뮬레이션 방법"]
