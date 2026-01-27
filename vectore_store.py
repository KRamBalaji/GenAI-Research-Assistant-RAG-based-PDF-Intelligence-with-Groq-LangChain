import os
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

def index_papers(papers_list, folder_path="faiss_index"):
    """FAISS-based vector index (cite: 248)."""
    # This model is free and runs on your CPU
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    
    all_chunks = []
    for paper in papers_list:
        chunks = text_splitter.create_documents(
            [s.content for s in paper.sections],
            metadatas=[{"title": paper.title, "paper_id": paper.paper_id} for _ in paper.sections]
        )
        all_chunks.extend(chunks)
    
    vectorstore = FAISS.from_documents(all_chunks, embeddings)
    vectorstore.save_local(folder_path)
    return vectorstore

def load_vector_db():
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    if os.path.exists("faiss_index"):
        return FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
    return None