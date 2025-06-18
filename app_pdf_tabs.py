import os
import uuid
import streamlit as st
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.llms import HuggingFaceHub
from dotenv import load_dotenv
import tempfile
from upload_faiss_to_blob import process_and_upload_pdf, list_uploaded_pdfs, download_faiss_index

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(page_title="Medical PDF Assistant", layout="wide")

# App title
st.title("Medical PDF Assistant")

# Initialize session state
if "active_pdfs" not in st.session_state:
    st.session_state.active_pdfs = {}

if "active_tab" not in st.session_state:
    st.session_state.active_tab = None

if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = {}

def load_pdf_retriever(upload_id):
    """Load FAISS index for a specific PDF from Azure Blob Storage"""
    # Download FAISS index from Azure Blob Storage
    faiss_dir = download_faiss_index(upload_id)
    
    if not faiss_dir:
        st.error(f"Failed to download FAISS index for PDF {upload_id}")
        return None
    
    try:
        # Initialize embeddings
        embeddings = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )
        
        # Load FAISS index
        vector_store = FAISS.load_local(faiss_dir, embeddings)
        
        # Create retriever
        retriever = vector_store.as_retriever(search_kwargs={"k": 5})
        
        return retriever
    except Exception as e:
        st.error(f"Error loading FAISS index: {str(e)}")
        return None

def create_qa_chain(retriever):
    """Create a QA chain with the given retriever"""
    # Initialize LLM
    hf_token = os.environ.get("HUGGINGFACE_API_TOKEN")
    
    if not hf_token:
        st.error("HuggingFace API token not found in environment variables")
        return None
    
    llm = HuggingFaceHub(
        repo_id="meta-llama/Llama-2-7b-hf", 
        model_kwargs={"temperature": 0.1}, 
        huggingfacehub_api_token=hf_token
    )
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True
    )
    
    return qa_chain

def process_uploaded_file(uploaded_file):
    """Process an uploaded PDF file"""
    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name
    
    try:
        # Process and upload PDF to Azure Blob Storage
        result = process_and_upload_pdf(tmp_path, uploaded_file.name)
        
        # Remove temporary file
        os.unlink(tmp_path)
        
        if not result:
            st.error("Failed to process and upload PDF")
            return None
        
        # Load retriever for the uploaded PDF
        retriever = load_pdf_retriever(result["id"])
        
        if not retriever:
            st.error("Failed to load retriever for the uploaded PDF")
            return None
        
        # Create QA chain
        qa_chain = create_qa_chain(retriever)
        
        if not qa_chain:
            st.error("Failed to create QA chain for the uploaded PDF")
            return None
        
        # Add PDF to active PDFs
        st.session_state.active_pdfs[result["id"]] = {
            "id": result["id"],
            "filename": result["filename"],
            "page_count": result["page_count"],
            "qa_chain": qa_chain
        }
        
        # Initialize messages for this PDF
        if result["id"] not in st.session_state.pdf_messages:
            st.session_state.pdf_messages[result["id"]] = []
        
        # Set as active tab
        st.session_state.active_tab = result["id"]
        
        return result["id"]
    
    except Exception as e:
        st.error(f"Error processing uploaded file: {str(e)}")
        # Remove temporary file if it exists
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return None

def load_existing_pdf(pdf_info):
    """Load an existing PDF from Azure Blob Storage"""
    # Check if PDF is already loaded
    if pdf_info["id"] in st.session_state.active_pdfs:
        st.session_state.active_tab = pdf_info["id"]
        return pdf_info["id"]
    
    # Load retriever for the PDF
    retriever = load_pdf_retriever(pdf_info["id"])
    
    if not retriever:
        st.error(f"Failed to load retriever for PDF {pdf_info['id']}")
        return None
    
    # Create QA chain
    qa_chain = create_qa_chain(retriever)
    
    if not qa_chain:
        st.error(f"Failed to create QA chain for PDF {pdf_info['id']}")
        return None
    
    # Add PDF to active PDFs
    st.session_state.active_pdfs[pdf_info["id"]] = {
        "id": pdf_info["id"],
        "filename": pdf_info["filename"],
        "page_count": pdf_info.get("page_count", "Unknown"),
        "qa_chain": qa_chain
    }
    
    # Initialize messages for this PDF
    if pdf_info["id"] not in st.session_state.pdf_messages:
        st.session_state.pdf_messages[pdf_info["id"]] = []
    
    # Set as active tab
    st.session_state.active_tab = pdf_info["id"]
    
    return pdf_info["id"]

def close_pdf_tab(pdf_id):
    """Close a PDF tab"""
    if pdf_id in st.session_state.active_pdfs:
        del st.session_state.active_pdfs[pdf_id]
    
    # Set active tab to another open PDF or None
    if st.session_state.active_tab == pdf_id:
        if st.session_state.active_pdfs:
            st.session_state.active_tab = next(iter(st.session_state.active_pdfs))
        else:
            st.session_state.active_tab = None

# Sidebar for PDF upload and management
with st.sidebar:
    st.header("PDF Management")
    
    # Upload new PDF
    uploaded_file = st.file_uploader("Upload a PDF", type="pdf")
    if uploaded_file:
        with st.spinner("Processing PDF..."):
            pdf_id = process_uploaded_file(uploaded_file)
            if pdf_id:
                st.success(f"Successfully uploaded and processed {uploaded_file.name}")
                # Clear file uploader
                uploaded_file = None
                st.experimental_rerun()
    
    # List existing PDFs from Azure Blob Storage
    st.subheader("Existing PDFs")
    
    # Refresh button
    if st.button("Refresh PDF List"):
        st.experimental_rerun()
    
    # Get list of PDFs from Azure Blob Storage
    existing_pdfs = list_uploaded_pdfs()
    
    if not existing_pdfs:
        st.info("No PDFs found in storage")
    else:
        for pdf in existing_pdfs:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"{pdf['filename']}", key=f"load_{pdf['id']}"):
                    with st.spinner("Loading PDF..."):
                        load_existing_pdf(pdf)
                        st.experimental_rerun()
            with col2:
                if pdf["id"] in st.session_state.active_pdfs:
                    st.write("✓ Open")

# Main content area
if not st.session_state.active_pdfs:
    st.info("Upload a PDF or select an existing one from the sidebar to get started")
else:
    # Create tabs for each active PDF
    tabs = st.tabs([pdf_info["filename"] for pdf_id, pdf_info in st.session_state.active_pdfs.items()])
    
    # Get list of PDF IDs in the same order as tabs
    pdf_ids = list(st.session_state.active_pdfs.keys())
    
    # Display content for each tab
    for i, (tab, pdf_id) in enumerate(zip(tabs, pdf_ids)):
        with tab:
            pdf_info = st.session_state.active_pdfs[pdf_id]
            
            # PDF information
            st.subheader(pdf_info["filename"])
            st.write(f"Pages: {pdf_info['page_count']}")
            
            # Close button
            if st.button("Close", key=f"close_{pdf_id}"):
                close_pdf_tab(pdf_id)
                st.experimental_rerun()
            
            # Display chat messages for this PDF
            for message in st.session_state.pdf_messages.get(pdf_id, []):
                with st.chat_message(message["role"]):
                    st.write(message["content"])
            
            # Chat input for this PDF
            prompt = st.chat_input(f"Ask a question about {pdf_info['filename']}...", key=f"input_{pdf_id}")
            
            if prompt:
                # Add user message to chat history
                st.session_state.pdf_messages[pdf_id].append({"role": "user", "content": prompt})
                
                # Display user message
                with st.chat_message("user"):
                    st.write(prompt)
                
                # Generate response
                with st.chat_message("assistant"):
                    with st.spinner("Thinking..."):
                        # Get QA chain for this PDF
                        qa_chain = pdf_info["qa_chain"]
                        
                        # Generate answer
                        response = qa_chain({"query": prompt})
                        answer = response["result"]
                        
                    st.write(answer)
                
                # Add assistant response to chat history
                st.session_state.pdf_messages[pdf_id].append({"role": "assistant", "content": answer})
                
                # Force a rerun to update the UI
                st.experimental_rerun()

if __name__ == "__main__":
    # This will be executed when the script is run directly
    pass