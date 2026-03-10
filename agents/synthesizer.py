from core.claude_runner import ClaudeRunner
from models.schemas import Idea, ResearchInput, ResearchProposal

class SynthesizerAgent:
    def __init__(self):
        self.claude = ClaudeRunner()

    def synthesize(self, research_input: ResearchInput, idea: Idea, references: list[str]) -> ResearchProposal:
        design_spec = self._generate_design_spec(research_input, idea)
        experiment_plan = self._generate_experiment_plan(research_input, idea)
        simulation = self._generate_simulation(research_input, idea)

        return ResearchProposal(
            title=f"{research_input.domain} - {idea.title}",
            input=research_input,
            selected_idea=idea,
            design_spec=design_spec,
            experiment_plan=experiment_plan,
            simulation_suggestion=simulation,
            references=references
        )

    def _generate_design_spec(self, ri: ResearchInput, idea: Idea) -> str:
        return self.claude.generate(f"""
공학 설계 사양서를 작성하세요.

도메인: {ri.domain}
목표: {ri.objective}
제약조건: {', '.join(ri.constraints)}
선택된 접근법: {idea.title} - {idea.approach}

다음을 포함한 상세 설계 사양서 (마크다운):
- 핵심 부품/재료 사양
- 성능 목표 수치
- 구조/회로 설명
- 예상 도전 과제
""")

    def _generate_experiment_plan(self, ri: ResearchInput, idea: Idea) -> str:
        return self.claude.generate(f"""
실험 계획서를 작성하세요.

아이디어: {idea.title}
목표: {ri.objective}

다음을 포함한 단계별 실험 계획 (마크다운):
- 1단계: 기초 특성 검증
- 2단계: 성능 최적화 실험
- 3단계: 환경 내성 테스트
- 측정 장비 및 방법
""")

    def _generate_simulation(self, ri: ResearchInput, idea: Idea) -> str:
        return self.claude.generate(f"""
시뮬레이션 방법을 제안하세요.

도메인: {ri.domain}
아이디어: {idea.title} - {idea.approach}

다음을 포함:
- 추천 시뮬레이션 도구 (SPICE, FDTD, FEM, Python 등)
- 핵심 시뮬레이션 파라미터
- 예시 Python 코드 스니펫 (있으면)
""")
