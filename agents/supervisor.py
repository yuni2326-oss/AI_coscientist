import re
from rich.console import Console
from rich.panel import Panel
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

        # Checkpoint #3 — 아이디어별 수정 루프
        self.checkpoint.checkpoint_num = 3
        total = len(proposals)
        for idx, proposal in enumerate(proposals, 1):
            round_num = 0
            while True:
                self._display_proposal(proposal, idx, total, round_num)
                feedback = self.checkpoint.ask(
                    "수정할 내용을 입력하세요 (없으면 Enter로 완료)"
                )
                if not feedback.strip():
                    break
                console.print("[bold green]재생성 중...[/bold green]")
                proposal = self.synthesizer.revise(proposal, feedback)
                round_num += 1
            proposals[idx - 1] = proposal

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

    def _display_proposal(self, proposal: ResearchProposal, idx: int, total: int, round_num: int):
        round_label = "최초" if round_num == 0 else f"수정 {round_num}회차"
        title = f"Checkpoint #3: 최종 검토 [{idx}/{total}] ({round_label})"
        content = (
            f"[bold]{proposal.title}[/bold]\n\n"
            f"[cyan]── 설계 사양 ──[/cyan]\n{proposal.design_spec}\n\n"
            f"[cyan]── 실험 계획 ──[/cyan]\n{proposal.experiment_plan}\n\n"
            f"[cyan]── 시뮬레이션 방법 ──[/cyan]\n{proposal.simulation_suggestion}"
        )
        console.print(Panel(content, title=f"[bold cyan]{title}[/bold cyan]"))
