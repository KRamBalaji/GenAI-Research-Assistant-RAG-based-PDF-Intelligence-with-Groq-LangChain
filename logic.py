import os
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_community.tools.tavily_search import TavilySearchResults 
from mcp_tools import get_mcp_tools
from typing import List, Dict
from langchain.tools import tool
from collections import Counter

load_dotenv()

# Initialize Groq LLM (Requirement 24: LangChain Orchestration)
llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.1-8b-instant", # Updated model name
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# --- MCP TOOLS FOR AGENTS ---

@tool
def paper_metadata_lookup(title_or_doi: str) -> dict:
    """Lookup paper year, venue, and citation count using title or DOI."""
    # Logic: In a real app, this calls an API like Semantic Scholar or CrossRef via MCP
    # Simulated response:
    return {
        "year": 2023,
        "venue": "CVPR",
        "citation_count": 150,
        "doi": "10.1101/example"
    }

@tool
def discovery_tool(paper_id: str) -> list:
    """Find semantically related papers and citation-based neighbors."""
    return ["Scaling Laws for LLMs", "Attention Is All You Need", "Llama 3 Technical Report"]

@tool
def trend_analytics_tool(topic: str) -> dict:
    """Returns publication frequency and emerging subtopics for a keyword."""
    return {
        "trend": [10, 25, 60, 150, 400], 
        "subtopics": ["Flash Attention", "Quantization", "PEFT"]
    }

# --- TREND IDENTIFICATION FUNCTION ---
def identify_emerging_trends(library):
    """Analyze keywords across library to find shifts in focus."""
    if not library:
        return []

    trends_by_year = {}
    for paper in library:
        year = str(paper.year)
        # Use content from the first section (usually abstract/intro)
        content = (paper.title + " " + paper.sections[0].content[:1000]).lower()
        
        # Simple keyword extraction: words longer than 6 chars
        words = [w.strip(".,()[]") for w in content.split() if len(w) > 6]
        
        if year not in trends_by_year:
            trends_by_year[year] = Counter()
        trends_by_year[year].update(words)

    years = sorted(trends_by_year.keys())
    emerging = []
    
    if years:
        latest_year = years[-1]
        # Get the top 5 most common words for the latest year
        for topic, count in trends_by_year[latest_year].most_common(5):
            growth = count
            if len(years) > 1:
                prev_year = years[-2]
                growth = count - trends_by_year[prev_year].get(topic, 0)
            
            # CRITICAL: This must be a dictionary
            emerging.append({
                "topic": topic.capitalize(),
                "growth": growth,
                "year": latest_year
            })

    return emerging

# --- 1. Summarization Feature (Part II) ---
def generate_summary(text: str, mode: str = "detailed"):
    templates = {
        "detailed": "Provide a 3-paragraph summary (Context, Methodology, Results): {text}",
        "short": "Provide a 1-sentence TL;DR: {text}"
    }
    prompt = ChatPromptTemplate.from_template(templates.get(mode, "detailed"))
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": text[:15000]})

# --- 2. RAG & Web Search Feature (Part IV) ---
def ask_with_web_search(query, vector_store, use_web=False):
    # 1. Retrieval from Vector Store (if it exists)
    if vector_store:
        docs = vector_store.similarity_search(query, k=3)
        paper_context = "\n".join([d.page_content for d in docs])
    else:
        docs = []
        paper_context = "No internal documents uploaded."

    # 2. Web Search logic (only triggers if toggle is ON)
    web_context = ""
    if use_web:
        search = TavilySearchResults(max_results=3)
        web_results = search.invoke(query)
        web_context = f"\n\nLATEST WEB UPDATES:\n{web_results}"

    prompt = ChatPromptTemplate.from_template("""
    Answer the question based on the context. 
    PAPER CONTEXT: {paper_context}
    {web_context}
    QUESTION: {query}
    """)
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"paper_context": paper_context, "web_context": web_context, "query": query}), docs

# --- 3. Cross-Paper Comparison (Part III.9) ---
def ask_cross_paper_question(query, papers, vector_store):
    docs = vector_store.similarity_search(query, k=5)
    context = "\n".join([d.page_content for d in docs])
    paper_titles = [p.title for p in papers]
    
    prompt = ChatPromptTemplate.from_template("""
    Compare these papers: {titles}
    Context: {context}
    Question: {query}
    Provide a comparative analysis (table or bullet points).
    """)
    
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"titles": ", ".join(paper_titles), "context": context, "query": query})

# --- 4. Trend Identification (Part V) ---
def identify_emerging_trends(papers):
    combined_text = " ".join([p.sections[0].content[:1000] for p in papers])
    prompt = ChatPromptTemplate.from_template("""
    Analyze these snippets and identify 3 Emerging Trends and 2 Declining Methods:
    {text}
    """)
    chain = prompt | llm | StrOutputParser()
    return chain.invoke({"text": combined_text[:20000]})

def extract_citations(text: str) -> list[str]:
    if not text or len(text) < 50:
        return []
        
    prompt = ChatPromptTemplate.from_template("""
    Extract only the titles of the research papers cited in the following text. 
    Return as a clean list with one title per line. No numbers, no authors.
    
    TEXT: {text}
    """)
    chain = prompt | llm | StrOutputParser()
    raw_titles = chain.invoke({"text": text})
    
    titles = [t.strip("- ").strip() for t in raw_titles.split("\n") if len(t.strip()) > 10]
    print(f"DEBUG: Extracted {len(titles)} citations.") # Check your terminal for this!
    return titles

def build_citation_graph(library):
    """Builds an adjacency list: Paper Title -> List of Cited Titles."""
    adj_list = {}
    for paper in library:
        adj_list[paper.title] = paper.references
    return adj_list