from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ResearchInput(BaseModel):
    domain: str          # 예: "광학 센서"
    objective: str       # 예: "저조도 환경 고감도 측정"
    constraints: list[str]  # 예: ["저전력", "소형화"]
    background: Optional[str] = None

class Idea(BaseModel):
    title: str
    description: str
    approach: str
    scores: dict[str, int] = {}  # 기술성숙도, 실현가능성, 독창성, 제약조건충족

class ResearchProposal(BaseModel):
    title: str
    input: ResearchInput
    selected_idea: Idea
    design_spec: str
    experiment_plan: str
    simulation_suggestion: str
    references: list[str]
    created_at: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
