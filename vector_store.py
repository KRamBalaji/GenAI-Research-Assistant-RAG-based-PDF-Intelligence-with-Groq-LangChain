from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document 
from models import ResearchPaper


def create_vector_store(paper: ResearchPaper):
    """
    Converts a ResearchPaper object into a FAISS vector store.
    """
    documents = []
    for section in paper.sections:
        # We wrap your paper sections into standard LangChain Document objects
        doc = Document(
            page_content=section.content,
            metadata={
                "section": section.section_title,
                "page": section.page_number
            }
        )
        documents.append(doc)
    
    # Initialize the Embedding Model (lightweight and runs on CPU)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    # Create the FAISS index
    vector_store = FAISS.from_documents(documents, embeddings)
    
    return vector_store