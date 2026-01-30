from pydantic import BaseModel, Field
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
    year: str = "Unknown"  # Part I: Metadata
    venue: str = "Unknown" # Part I: Metadata
    # Part IV: Citation Graph Support
    references: List[str] = [Field(default_factory=list)] # Extracted bibliography
    citations: int = 0  # External citation count (simulated or API)