from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm

console = Console()

class HumanCheckpoint:
    def __init__(self, checkpoint_num: int = 0):
        self.checkpoint_num = checkpoint_num

    def display(self, title: str, content: str):
        console.print(Panel(content, title=f"[bold cyan]Checkpoint #{self.checkpoint_num}: {title}[/bold cyan]"))

    def ask(self, question: str) -> str:
        return Prompt.ask(f"\n[yellow]{question}[/yellow]")

    def confirm(self, question: str) -> bool:
        return Confirm.ask(f"\n[yellow]{question}[/yellow]")
