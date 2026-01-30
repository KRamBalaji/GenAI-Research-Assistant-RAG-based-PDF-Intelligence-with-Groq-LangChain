from langchain_core.tools import tool
import random

@tool
def metadata_lookup_tool(title: str):
    """
    MCP Tool 1: Paper Metadata Lookup
    Input: Paper Title
    Output: Metadata (Year, Venue, Citation Count)
    """
    return {
        "year": random.randint(2018, 2024),
        "venue": random.choice(["NeurIPS", "CVPR", "ICLR", "Nature"]),
        "citation_count": random.randint(5, 500)
    }

@tool
def related_work_tool(paper_id: str):
    """MCP Tool 2: Related Work Discovery"""
    return ["Attention is All You Need", "BERT", "GPT-4"]

@tool
def trend_analytics_tool(topic: str):
    """MCP Tool 3: Trend Analytics"""
    return {"topic": topic, "growth_rate": "+150% YoY"}

def get_mcp_tools():
    return [metadata_lookup_tool, related_work_tool, trend_analytics_tool]