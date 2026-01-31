import os
import re
from langchain_community.document_loaders import PyPDFLoader
from models import ResearchPaper, PaperSection

def parse_paper_to_sections(file_path):
    loader = PyPDFLoader(file_path)
    pages = loader.load()
    
    sections = []
    full_text = ""
    
    # Part I: Section-Level Extraction
    for i, page in enumerate(pages):
        content = page.page_content
        full_text += content + "\n"
        sections.append(PaperSection(
            section_title=f"Page {i+1}",
            content=content,
            page_number=i+1
        ))
        
    # Part IV: Citation Parsing
    refs = extract_references(full_text)
    
    # Basic Metadata Extraction (Heuristic)
    title = os.path.basename(file_path).replace(".pdf", "")
    
    return ResearchPaper(
        title=title,
        authors=["Unknown Author"], # In real prod, use Groq to extract this
        year="2024", 
        venue="ArXiv",
        sections=sections,
        references=refs
    )

def extract_references(text):
    """
    Naive regex to extract lines looking like citations [1] Author...
    """
    # Look for the References header
    ref_split = re.split(r'(?i)\n\s*references\s*\n', text)
    if len(ref_split) < 2:
        return []
    
    ref_text = ref_split[-1]
    # Find patterns like [1], 1., (Author, Year)
    citations = re.findall(r'\[\d+\]\s.*?(?=\[\d+\]|$)', ref_text, re.DOTALL)
    return [c.strip().replace('\n', ' ') for c in citations[:20]] # Limit to top 20