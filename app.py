import streamlit as st
import os
import graphviz
import pandas as pd
import plotly.express as px
from ingestion import parse_paper_to_sections
from vector_store import create_vector_store
from logic import (
    generate_summary, 
    ask_cross_paper_question, 
    ask_with_web_search, 
    extract_citations, 
    build_citation_graph, 
    identify_emerging_trends
)
from mcp_tools import metadata_lookup_tool

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Research Assistant", layout="wide", initial_sidebar_state="expanded")

# Gemini-style CSS Fixes
st.markdown("""
    <style>
    .block-container { padding-bottom: 0rem !important; }
    [data-testid="stBottomBlockContainer"] {
        gap: 0.5rem !important;
        padding-bottom: 2rem !important;
        background-color: transparent !important;
    }
    .stChatMessage { border-radius: 15px; margin-bottom: 10px; }
    .main-header { font-size: 2.2rem; font-weight: 700; text-align: center; margin-bottom: 10px; color: #4285F4; }
    footer { visibility: hidden; height: 0px; }
    
    /* Smooth tab styling */
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state: st.session_state.messages = [] 
if "library" not in st.session_state: st.session_state.library = [] 
if "vs" not in st.session_state: st.session_state.vs = None

# --- 2. SIDEBAR: Document Management ---
with st.sidebar:
    st.title("📚 Research Library")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    
    if uploaded_file:
        if not os.path.exists("temp"): os.makedirs("temp")
        path = f"temp/{uploaded_file.name}"
        with open(path, "wb") as f: f.write(uploaded_file.getbuffer())
        
        if st.button("➕ Index Paper"):
            with st.spinner("Processing..."):
                paper = parse_paper_to_sections(path)
                
                # Metadata & Citation logic
                ref_text = ""
                for s in paper.sections:
                    label = getattr(s, 'name', getattr(s, 'heading', getattr(s, 'title', ""))).lower()
                    if any(kw in label for kw in ["reference", "bibliography", "works cited"]):
                        ref_text += s.content + "\n"
                
                if ref_text:
                    paper.references = extract_citations(ref_text[:7000])
                
                st.session_state.library.append(paper)
                st.session_state.vs = create_vector_store(paper)
                st.success(f"Added: {paper.title}")

    if st.session_state.library:
        st.divider()
        st.subheader("Manage Library")
        for idx, p in enumerate(st.session_state.library):
            cols = st.columns([0.8, 0.2])
            cols[0].caption(f"• {p.title} ({p.year})")
            if cols[1].button("🗑️", key=f"del_{idx}"):
                st.session_state.library.pop(idx)
                st.rerun()

# --- 3. MAIN UI: TABS ---
st.markdown('<div class="main-header">Research Intelligence Assistant</div>', unsafe_allow_html=True)

tab_chat, tab_intel = st.tabs(["💬 Conversation", "🧠 Intelligence Dashboard"])

with tab_chat:
    # Scrollable Chat History
    chat_container = st.container(height=550, border=False)
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 Welcome! Upload a paper or ask a question to get started.")
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

# --- 4. UNIFIED BOTTOM AREA ---
from streamlit import _bottom
with _bottom:
    use_web = st.toggle("🌍 Search Web (Tavily)", value=False)
    
    if st.session_state.library:
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("📝 Summarize Latest", use_container_width=True):
                last_p = st.session_state.library[-1]
                summary = generate_summary(last_p.sections[0].content, "detailed")
                st.session_state.messages.append({"role": "assistant", "content": f"**Summary of {last_p.title}:**\n\n{summary}"})
                st.rerun()
        with col_btn2:
            if st.button("📊 Compare All Papers", use_container_width=True):
                res = ask_cross_paper_question("Compare goals and methods.", st.session_state.library, st.session_state.vs)
                st.session_state.messages.append({"role": "assistant", "content": res})
                st.rerun()

    if prompt := st.chat_input("Ask a research question..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat_container:
            with st.chat_message("user"): st.markdown(prompt)
        
        with chat_container:
            with st.chat_message("assistant"):
                with st.spinner("Analyzing..."):
                    response, sources = ask_with_web_search(prompt, st.session_state.vs, use_web=use_web)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

with tab_intel:
    if not st.session_state.library:
        st.info("Upload and index papers to unlock the Intelligence Dashboard.")
    else:
        # --- ROW 1: EMERGING TOPICS (Metrics) ---
        st.subheader("🔥 Emerging Research Trends")
        trends = identify_emerging_trends(st.session_state.library)
        if trends and isinstance(trends, list):
            # Filter out anything that isn't a dictionary to prevent AttributeErrors
            valid_trends = [t for t in trends if isinstance(t, dict)]
            
            if valid_trends:
                trend_cols = st.columns(min(len(valid_trends), 4))
                for i, t in enumerate(valid_trends[:4]):
                    with trend_cols[i]:
                        st.metric(
                            label=f"Topic: {t.get('topic', 'N/A')}", 
                            value=t.get('year', 'N/A'), 
                            delta=f"+{t.get('growth', 0)} hits"
                        )
        
        st.divider()

        # --- ROW 2: VISUALIZATIONS (Side-by-Side) ---
        vis_col1, vis_col2 = st.columns(2)

        with vis_col1:
            st.subheader("📈 Publication Frequency")
            trend_data = [{"Year": p.year, "Count": 1} for p in st.session_state.library]
            df_trends = pd.DataFrame(trend_data).groupby("Year").count().reset_index()
            fig = px.line(df_trends, x="Year", y="Count", markers=True, template="plotly_white")
            fig.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=300)
            st.plotly_chart(fig, use_container_width=True)

        with vis_col2:
            st.subheader("🕸️ Citation Network")
            dot = graphviz.Digraph()
            dot.attr(rankdir='LR', size='5,5', bgcolor='transparent')
            for paper in st.session_state.library:
                dot.node(paper.title, paper.title[:15] + "...", shape="box", style="rounded,filled", fillcolor="#E1F5FE")
                for ref in paper.references[:2]:
                    dot.edge(paper.title, ref[:15] + "...")
            st.graphviz_chart(dot, use_container_width=True)

        # --- ROW 3: DETAILED TABLE ---
        st.subheader("📊 Citation Data Table")
        graph_data = build_citation_graph(st.session_state.library)
        table_rows = []
        for paper, refs in graph_data.items():
            for r in refs:
                table_rows.append({"Source Paper": paper, "Connection": "➡️ cites", "Reference": r})
        
        if table_rows:
            st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)