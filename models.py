from pydantic import BaseModel
from typing import List, Optional

class PaperSection(BaseModel):
    section_title: str
    content: str

class ResearchPaper(BaseModel):
    paper_id: str
    title: str
    authors: List[str]
    abstract: str
    sections: List[PaperSection]