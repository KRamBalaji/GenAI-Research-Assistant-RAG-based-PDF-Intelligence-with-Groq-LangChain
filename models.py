from pydantic import BaseModel, Field
from typing import List, Optional

class PaperSection(BaseModel):
    section_title: str
    content: str
    page_number: int

class ResearchPaper(BaseModel):
    title: str
    authors: List[str]
    sections: List[PaperSection]
    year: str = "Unknown"  # Part I: Metadata
    venue: str = "Unknown" # Part I: Metadata
    metadata: dict = Field(default_factory=dict)
    # Part IV: Citation Graph Support
    references: List[str] = [Field(default_factory=list)] # Extracted bibliography
    citations: int = 0  # External citation count (simulated or API)