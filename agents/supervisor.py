import re
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

    def run(self, research_input: ResearchInput) -> list[ResearchProposal]:
        console.print("\n[bold green]1. 아이디어 생성 중...[/bold green]")
        ideas = self.generator.generate(research_input)

        console.print("[bold green]2. 아이디어 평가 중...[/bold green]")
        ideas = self.critic.score_all(ideas, research_input)

        self._display_ideas(ideas)

        # Checkpoint #1 — 복수 선택
        self.checkpoint.checkpoint_num = 1
        self.checkpoint.display("아이디어 선택", "위 아이디어들을 검토하세요.")
        feedback = self.checkpoint.ask(
            "어떤 아이디어를 선택하시겠습니까? (번호를 쉼표/공백으로 구분, 예: 1,3 또는 1 2)"
        )
        selected_ideas = self._select_ideas(ideas, feedback)

        proposals = []
        for i, selected in enumerate(selected_ideas, 1):
            console.print(f"\n[bold green]3-{i}. [{selected.title}] 문헌 검색 중...[/bold green]")
            references = self.literature.find_references(selected, research_input)

            # Checkpoint #2 — 아이디어별
            self.checkpoint.checkpoint_num = 2
            self.checkpoint.display(
                f"참고문헌 확인 [{selected.title}]", "\n".join(references)
            )
            if not self.checkpoint.confirm("이 참고문헌으로 계속하시겠습니까?"):
                extra = self.checkpoint.ask("추가할 참고문헌이 있으면 입력하세요 (없으면 Enter)")
                if extra:
                    references.append(extra)

            console.print(f"[bold green]4-{i}. [{selected.title}] 제안서 작성 중...[/bold green]")
            proposal = self.synthesizer.synthesize(research_input, selected, references)
            proposals.append(proposal)

        # Checkpoint #3 — 전체 완료 후 한 번
        self.checkpoint.checkpoint_num = 3
        summary = "\n\n".join(
            f"[{p.selected_idea.title}]\n{p.design_spec[:200]}..." for p in proposals
        )
        self.checkpoint.display("최종 검토", summary)
        self.checkpoint.confirm("제안서 생성을 완료하시겠습니까?")

        return proposals

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

    def _select_ideas(self, ideas: list[Idea], feedback: str) -> list[Idea]:
        # 번호 파싱 (쉼표 또는 공백 구분)
        nums = [int(n) for n in re.findall(r'\d+', feedback) if 1 <= int(n) <= len(ideas)]
        if nums:
            seen = set()
            result = []
            for n in nums:
                if n not in seen:
                    seen.add(n)
                    result.append(ideas[n - 1])
            return result
        # 제목 매칭
        matched = [idea for idea in ideas if idea.title in feedback]
        if matched:
            return matched
        # fallback: 최고점 1개
        return [max(ideas, key=lambda x: sum(x.scores.values()), default=ideas[0])]
