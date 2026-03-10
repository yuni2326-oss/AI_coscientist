from rich.console import Console
from rich.table import Table
from agents.generator import GeneratorAgent
from agents.critic import CriticAgent
from agents.literature import LiteratureAgent
from agents.synthesizer import SynthesizerAgent
from core.checkpoint import HumanCheckpoint
from models.schemas import ResearchInput, Idea, ResearchProposal

console = Console()

class SupervisorAgent:
    def __init__(self):
        self.generator = GeneratorAgent()
        self.critic = CriticAgent()
        self.literature = LiteratureAgent()
        self.synthesizer = SynthesizerAgent()
        self.checkpoint = HumanCheckpoint()

    def run(self, research_input: ResearchInput) -> ResearchProposal:
        console.print("\n[bold green]1. 아이디어 생성 중...[/bold green]")
        ideas = self.generator.generate(research_input)

        console.print("[bold green]2. 아이디어 평가 중...[/bold green]")
        ideas = self.critic.score_all(ideas, research_input)

        self._display_ideas(ideas)

        # Checkpoint #1
        self.checkpoint.checkpoint_num = 1
        self.checkpoint.display("아이디어 선택", "위 아이디어들을 검토하세요.")
        feedback = self.checkpoint.ask("어떤 아이디어를 선택/수정하시겠습니까? (제목 또는 피드백 입력)")
        selected = self._select_idea(ideas, feedback)

        console.print("\n[bold green]3. 문헌 검색 중...[/bold green]")
        references = self.literature.find_references(selected, research_input)

        # Checkpoint #2
        self.checkpoint.checkpoint_num = 2
        self.checkpoint.display("참고문헌 확인", "\n".join(references))
        if not self.checkpoint.confirm("이 참고문헌으로 계속하시겠습니까?"):
            extra = self.checkpoint.ask("추가할 참고문헌이 있으면 입력하세요 (없으면 Enter)")
            if extra:
                references.append(extra)

        console.print("\n[bold green]4. 최종 제안서 작성 중...[/bold green]")
        proposal = self.synthesizer.synthesize(research_input, selected, references)

        # Checkpoint #3
        self.checkpoint.checkpoint_num = 3
        self.checkpoint.display("최종 검토", proposal.design_spec[:300] + "...")
        self.checkpoint.confirm("제안서 생성을 완료하시겠습니까?")

        return proposal

    def _display_ideas(self, ideas: list[Idea]):
        table = Table(title="생성된 아이디어")
        table.add_column("번호", style="cyan")
        table.add_column("제목", style="white")
        table.add_column("기술성숙도", justify="center")
        table.add_column("실현가능성", justify="center")
        table.add_column("독창성", justify="center")
        for i, idea in enumerate(ideas, 1):
            table.add_row(
                str(i), idea.title,
                str(idea.scores.get("기술성숙도", "-")),
                str(idea.scores.get("실현가능성", "-")),
                str(idea.scores.get("독창성", "-"))
            )
        console.print(table)

    def _select_idea(self, ideas: list[Idea], feedback: str) -> Idea:
        for idea in ideas:
            if idea.title in feedback:
                return idea
        for i, idea in enumerate(ideas, 1):
            if str(i) in feedback:
                return idea
        # 점수 합계 기준 최고 아이디어 반환
        return max(ideas, key=lambda x: sum(x.scores.values()), default=ideas[0])
