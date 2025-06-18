import os
import streamlit as st
import tempfile
import shutil
import zipfile
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(page_title="Medical Gynecology Assistant", layout="wide")

# App title
st.title("Medical Gynecology Assistant")

# Initialize session state for conversation history
if "messages" not in st.session_state:
    st.session_state.messages = []

@st.cache_resource
def load_retriever():
    """Load FAISS index from local storage or Azure Blob Storage"""
    # Check if we should use Azure Blob Storage
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    use_blob_storage = connection_string and container_name
    
    # Create embeddings model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    if use_blob_storage:
        try:
            # Create a temporary directory to store downloaded index
            temp_dir = tempfile.mkdtemp()
            zip_path = os.path.join(temp_dir, "faiss_index.zip")
            extracted_dir = os.path.join(temp_dir, "faiss_index")
            
            # Download from Azure Blob Storage
            with st.spinner("Downloading FAISS index from Azure Blob Storage..."):
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                container_client = blob_service_client.get_container_client(container_name)
                
                # Try to download the zip file first
                try:
                    with open(zip_path, "wb") as download_file:
                        download_file.write(container_client.download_blob("faiss_index.zip").readall())
                    
                    # Extract the zip file
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(temp_dir)
                    
                    # Load the index
                    vector_store = FAISS.load_local(extracted_dir, embeddings)
                    st.sidebar.success("Loaded FAISS index from Azure Blob Storage (zip)")
                
                except Exception as e:
                    # If zip download fails, try individual files
                    st.sidebar.warning(f"Could not download zip file: {str(e)}")
                    st.sidebar.info("Trying to download individual files...")
                    
                    # Create directory for extracted files
                    os.makedirs(extracted_dir, exist_ok=True)
                    
                    # Download index.faiss
                    with open(os.path.join(extracted_dir, "index.faiss"), "wb") as download_file:
                        download_file.write(container_client.download_blob("faiss_index/index.faiss").readall())
                    
                    # Download index.pkl
                    with open(os.path.join(extracted_dir, "index.pkl"), "wb") as download_file:
                        download_file.write(container_client.download_blob("faiss_index/index.pkl").readall())
                    
                    # Load the index
                    vector_store = FAISS.load_local(extracted_dir, embeddings)
                    st.sidebar.success("Loaded FAISS index from Azure Blob Storage (individual files)")
            
        except Exception as e:
            st.sidebar.error(f"Error loading from Azure Blob Storage: {str(e)}")
            # Fall back to local index if available
            if os.path.exists("faiss_index"):
                vector_store = FAISS.load_local("faiss_index", embeddings)
                st.sidebar.warning("Failed to load from Blob Storage. Using local FAISS index instead.")
            else:
                st.sidebar.error("No FAISS index found locally or in Blob Storage. Please run preprocess.py first.")
                st.stop()
    
    elif os.path.exists("faiss_index"):
        # Load existing local index
        vector_store = FAISS.load_local("faiss_index", embeddings)
        st.sidebar.info("Loaded local FAISS index (Azure Blob Storage not configured)")
    else:
        st.sidebar.error("No local FAISS index found. Please run preprocess.py first.")
        st.stop()
    
    # Create retriever
    retriever = vector_store.as_retriever(search_kwargs={"k": 5})
    return retriever

@st.cache_resource
def create_azure_openai_client():
    """Create Azure OpenAI client"""
    try:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = os.environ.get("AZURE_OPENAI_KEY")
        api_version = "2023-05-15"  # Using an older version for compatibility
        
        # Simpler initialization for older OpenAI versions
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        return client
    except Exception as e:
        st.error(f"Error creating Azure OpenAI client: {str(e)}")
        return None

def call_azure_openai(prompt):
    """Call Azure OpenAI service using the official client"""
    try:
        client = create_azure_openai_client()
        if not client:
            return "Azure OpenAI client could not be created. Check your credentials."
        
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo")
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical assistant specializing in gynecology. Provide clear, accurate information based on medical literature. Include relevant details and maintain a professional tone."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=800,
            temperature=0.3,
            model=deployment
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"Error: {str(e)}"

def generate_answer(question, docs):
    """Generate an answer based on retrieved documents"""
    # Extract content and citations
    contexts = []
    citations = []
    
    for i, doc in enumerate(docs):
        source = os.path.basename(doc.metadata.get('source', 'unknown'))
        page = doc.metadata.get('page', 'unknown')
        citation = f"[{i+1}] {source}, page {page}"
        
        contexts.append(doc.page_content)
        citations.append(citation)
    
    # Combine contexts
    full_context = "\n\n".join([f"Document {i+1} (from {os.path.basename(doc.metadata.get('source', 'unknown'))}, page {doc.metadata.get('page', 'unknown')}):\n{doc.page_content}" for i, doc in enumerate(docs)])
    
    # Create prompt for Azure OpenAI
    prompt = f"""
    Based on the following medical literature, answer this question: {question}
    
    Medical literature:
    {full_context}
    
    Provide a detailed and accurate answer based only on the information in the medical literature. 
    Include citations like [1], [2], etc. when referencing specific information from the documents.
    """
    
    # Generate summary using Azure OpenAI
    summary = call_azure_openai(prompt)
    
    # Format answer with citations
    answer = f"**Question:** {question}\n\n**Answer:** {summary}\n\n**Sources:**\n"
    for citation in citations:
        answer += f"- {citation}\n"
    
    return answer

# Sidebar information
with st.sidebar:
    st.header("About")
    st.write("This application uses RAG to answer questions about gynecology based on medical textbooks.")
    
    # Load retriever on app startup
    with st.spinner("Loading medical knowledge base..."):
        retriever = load_retriever()
    
    st.success("Medical knowledge base loaded!")
    
    # Azure OpenAI status
    if os.environ.get("AZURE_OPENAI_ENDPOINT") and os.environ.get("AZURE_OPENAI_KEY"):
        st.success("Azure OpenAI connected")
    else:
        st.warning("Azure OpenAI not configured - set environment variables")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask a question about gynecology"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Display user message
    with st.chat_message("user"):
        st.write(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        with st.spinner("Generating answer..."):
            # Get relevant documents
            docs = retriever.get_relevant_documents(prompt)
            
            # Generate answer
            response = generate_answer(prompt, docs)
            
        st.markdown(response)
    
    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": response})