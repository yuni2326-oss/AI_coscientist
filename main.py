import os
try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.prompt import Prompt
from models.schemas import ResearchInput, ResearchProposal
from agents.supervisor import SupervisorAgent
from config import settings

console = Console()

def collect_input() -> ResearchInput:
    console.print("\n[bold cyan]=== AI Co-Scientist for Engineering ===[/bold cyan]\n")
    domain = Prompt.ask("[white]연구 도메인[/white]", default="광학 센서")
    objective = Prompt.ask("[white]연구 목표[/white]")
    constraints_raw = Prompt.ask("[white]제약조건 (쉼표로 구분)[/white]", default="저전력, 소형화")
    constraints = [c.strip() for c in constraints_raw.split(",")]
    background = Prompt.ask("[white]배경 정보 (없으면 Enter)[/white]", default="")
    return ResearchInput(
        domain=domain,
        objective=objective,
        constraints=constraints,
        background=background or None
    )

def save_proposal(proposal: ResearchProposal, output_dir: str = None) -> Path:
    output_dir = Path(output_dir or settings.output_dir)
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_{proposal.input.domain.replace(' ', '_')}.md"
    filepath = output_dir / filename

    content = f"""# {proposal.title}

**생성일시:** {proposal.created_at}
**도메인:** {proposal.input.domain}
**목표:** {proposal.input.objective}
**제약조건:** {', '.join(proposal.input.constraints)}

---

## 선택된 접근법

**{proposal.selected_idea.title}**

{proposal.selected_idea.description}

접근법: {proposal.selected_idea.approach}

---

## 설계 사양

{proposal.design_spec}

---

## 실험 계획

{proposal.experiment_plan}

---

## 시뮬레이션 방법

{proposal.simulation_suggestion}

---

## 참고문헌

{chr(10).join(proposal.references)}
"""
    filepath.write_text(content, encoding="utf-8")
    return filepath

def main():
    research_input = collect_input()
    supervisor = SupervisorAgent()
    proposal = supervisor.run(research_input)
    output_file = save_proposal(proposal)
    console.print(f"\n[bold green]제안서 저장 완료: {output_file}[/bold green]")

if __name__ == "__main__":
    main()
