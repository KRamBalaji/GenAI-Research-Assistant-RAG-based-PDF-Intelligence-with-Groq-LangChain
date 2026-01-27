import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

load_dotenv()

# Initialize Groq LLM (Requirement 24: LangChain Orchestration)
llm = ChatGroq(
    temperature=0, 
    model_name="llama-3.1-8b-instant", # Updated model name
    groq_api_key=os.getenv("GROQ_API_KEY")
)

# This name MUST match the import in app.py
def generate_structured_summary(text_content):
    """Generates a structured summary (cite: 125, 134)."""
    prompt = ChatPromptTemplate.from_template("""
    You are a research assistant. Provide a summary with technical accuracy (cite: 136).
    Include: Problem Statement, Proposed Approach, Key Contributions, and Results (cite: 127-131).
    
    Content: {text}
    """)
    chain = prompt | llm | StrOutputParser()
    # Limit text to 15000 chars to stay within token limits
    return chain.invoke({"text": text_content[:15000]})

def get_rag_chain(vectorstore):
    """Context-Aware Question Answering pipeline (cite: 139, 145)."""
    retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    
    template = """Answer the research question based ONLY on the following context:
    {context}
    
    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)
    
    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])
    
    # Requirement 148: Generate grounded answers using LangChain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain