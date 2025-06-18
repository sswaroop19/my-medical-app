import os
import tempfile
from flask import Flask, render_template, request, jsonify, Response
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from openai import AzureOpenAI
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder='static')
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "medical_assistant_secret_key")

# Initialize global variables
retriever = None
azure_client = None

def load_faiss_from_blob():
    """Load FAISS index from Azure Blob Storage"""
    connection_string = os.environ.get("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.environ.get("BLOB_CONTAINER_NAME")
    
    if not connection_string or not container_name:
        print("Azure Storage credentials not found, checking for local index")
        return load_faiss_local()
    
    # Create embeddings model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    try:
        # Create a temporary directory to store downloaded index
        temp_dir = tempfile.mkdtemp()
        extracted_dir = os.path.join(temp_dir, "faiss_index")
        os.makedirs(extracted_dir, exist_ok=True)
        
        # Download from Azure Blob Storage
        print("Downloading FAISS index from Azure Blob Storage...")
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        # Download index.faiss
        with open(os.path.join(extracted_dir, "index.faiss"), "wb") as download_file:
            download_file.write(container_client.download_blob("faiss_index/index.faiss").readall())
        
        # Download index.pkl
        with open(os.path.join(extracted_dir, "index.pkl"), "wb") as download_file:
            download_file.write(container_client.download_blob("faiss_index/index.pkl").readall())
        
        # Load the index
        vector_store = FAISS.load_local(extracted_dir, embeddings)
        print("Loaded FAISS index from Azure Blob Storage")
        
        # Create retriever
        return vector_store.as_retriever(search_kwargs={"k": 5})
        
    except Exception as e:
        print(f"Error loading from Azure Blob Storage: {str(e)}")
        # Fall back to local index
        return load_faiss_local()

def load_faiss_local():
    """Load FAISS index from local storage"""
    if not os.path.exists("faiss_index"):
        raise Exception("No FAISS index found locally. Please run preprocess.py first.")
    
    # Create embeddings model
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'}
    )
    
    # Load the index
    vector_store = FAISS.load_local("faiss_index", embeddings)
    print("Loaded local FAISS index")
    
    # Create retriever
    return vector_store.as_retriever(search_kwargs={"k": 5})

def create_azure_openai_client():
    """Create Azure OpenAI client"""
    try:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        api_key = os.environ.get("AZURE_OPENAI_KEY")
        api_version = "2023-05-15"
        
        client = AzureOpenAI(
            azure_endpoint=endpoint,
            api_key=api_key,
            api_version=api_version
        )
        return client
    except Exception as e:
        print(f"Error creating Azure OpenAI client: {str(e)}")
        return None

def search_web(query, max_results=3):
    """Search the web for medical information"""
    try:
        # In a real application, you would integrate with a search API like Bing or Google
        # For now, we'll use a simple dictionary of medical topics
        medical_topics = {
            "pcos": [
                {
                    'title': "Polycystic ovary syndrome (PCOS) - Mayo Clinic",
                    'body': "Polycystic ovary syndrome (PCOS) is a hormonal disorder common among women of reproductive age. Women with PCOS may have infrequent or prolonged menstrual periods or excess male hormone (androgen) levels.",
                    'href': "https://www.mayoclinic.org/diseases-conditions/pcos/symptoms-causes/syc-20353439",
                    'source': "Web Search Result #1",
                    'image': "https://www.mayoclinic.org/-/media/kcms/gbs/patient-consumer/images/2013/11/15/17/35/ds00423_-ds00430_-ds00693_-ds00856_-ds00946_-ds01047_im00211_r7_polycysticthu_jpg.jpg"
                },
                {
                    'title': "PCOS (Polycystic Ovary Syndrome) - Cleveland Clinic",
                    'body': "PCOS is a common hormone disorder that affects 6% to 12% of people with female sex organs who are of reproductive age. It's also a leading cause of infertility.",
                    'href': "https://my.clevelandclinic.org/health/diseases/8316-polycystic-ovary-syndrome-pcos",
                    'source': "Web Search Result #2",
                    'image': "https://my.clevelandclinic.org/-/scassets/images/org/health/articles/8316-polycystic-ovary-syndrome-pcos"
                }
            ],
            "endometriosis": [
                {
                    'title': "Endometriosis - Symptoms and causes - Mayo Clinic",
                    'body': "Endometriosis is a condition in which cells similar to those that line the uterus, the endometrial cells, grow outside the uterus. Endometriosis most commonly affects the ovaries, fallopian tubes and tissue lining the pelvis.",
                    'href': "https://www.mayoclinic.org/diseases-conditions/endometriosis/symptoms-causes/syc-20354656",
                    'source': "Web Search Result #1",
                    'image': "https://www.mayoclinic.org/-/media/kcms/gbs/patient-consumer/images/2013/11/15/17/37/ds00289_im03430_ww5r8y1t_jpg.jpg"
                }
            ],
            "pregnancy": [
                {
                    'title': "Pregnancy - Office on Women's Health",
                    'body': "Pregnancy is the term used to describe the period in which a fetus develops inside a woman's womb or uterus. Pregnancy usually lasts about 40 weeks, or just over 9 months.",
                    'href': "https://www.womenshealth.gov/pregnancy",
                    'source': "Web Search Result #1",
                    'image': "https://www.womenshealth.gov/files/styles/large/public/images/jogging-while-pregnant.jpg"
                }
            ],
            "menopause": [
                {
                    'title': "Menopause - Symptoms and causes - Mayo Clinic",
                    'body': "Menopause is the time that marks the end of your menstrual cycles. It's diagnosed after you've gone 12 months without a menstrual period. Menopause can happen in your 40s or 50s.",
                    'href': "https://www.mayoclinic.org/diseases-conditions/menopause/symptoms-causes/syc-20353397",
                    'source': "Web Search Result #1",
                    'image': "https://www.mayoclinic.org/-/media/kcms/gbs/patient-consumer/images/2013/11/15/17/39/ds00119_im03468_mcdc7_menopausethu_jpg.jpg"
                }
            ],
            "gynecology": [
                {
                    'title': "Gynecology - Mayo Clinic",
                    'body': "Gynecology is the medical practice dealing with the health of the female reproductive system. Almost all modern gynecologists are also obstetricians.",
                    'href': "https://www.mayoclinic.org/departments-centers/obstetrics-gynecology/sections/overview/ovc-20264296",
                    'source': "Web Search Result #1",
                    'image': "https://www.mayoclinic.org/-/media/kcms/gbs/patient-consumer/images/2019/04/03/20/58/gynecology-8col.jpg"
                }
            ]
        }
        
        # Try to match the query to one of our topics
        query_lower = query.lower()
        results = []
        
        # Check if any of our topics are in the query
        for topic, topic_results in medical_topics.items():
            if topic in query_lower:
                results.extend(topic_results[:max_results])
                break
        
        # If no specific topic matched, use the general gynecology results
        if not results:
            results = medical_topics["gynecology"][:max_results]
        
        # Add a general medical resource as the last result if we have space
        if len(results) < max_results:
            results.append({
                'title': "MedlinePlus - Health Information from the National Library of Medicine",
                'body': "MedlinePlus is an online health information resource for patients and their families and friends. It is a service of the National Library of Medicine (NLM), the world's largest medical library.",
                'href': "https://medlineplus.gov/",
                'source': f"Web Search Result #{len(results)+1}",
                'image': "https://medlineplus.gov/images/homepage/medlineplus-social.jpg"
            })
        
        return results
        
    except Exception as e:
        print(f"Web search error: {str(e)}")
        # Return fallback results
        return [
            {
                'title': "Mayo Clinic - Gynecology",
                'body': "Mayo Clinic gynecologists provide comprehensive care for women, including routine and complex gynecology services.",
                'href': "https://www.mayoclinic.org/departments-centers/obstetrics-gynecology/sections/overview/ovc-20264296",
                'source': "Web Search Result #1",
                'image': "https://www.mayoclinic.org/-/media/kcms/gbs/patient-consumer/images/2019/04/03/20/58/gynecology-8col.jpg"
            }
        ]

def generate_answer(question, docs, web_search_enabled=True):
    """Generate an answer based on retrieved documents and web search"""
    # Extract content and citations from documents
    contexts = []
    citations = []
    
    for i, doc in enumerate(docs):
        source = os.path.basename(doc.metadata.get('source', 'unknown'))
        page = doc.metadata.get('page', 'unknown')
        citation = f"[{i+1}] {source}, page {page}"
        
        contexts.append(doc.page_content)
        citations.append(citation)
    
    # Get web search results if enabled
    web_results = search_web(question) if web_search_enabled else []
    
    # Add web results to context and citations
    for i, result in enumerate(web_results):
        web_context = f"Title: {result['title']}\nContent: {result['body']}\nURL: {result['href']}"
        contexts.append(web_context)
        # Format web citations consistently for easier parsing in the frontend
        # Include image URL in the citation for the frontend to use
        image_url = result.get('image', '')
        citations.append(f"[{len(docs) + i + 1}] Web Search Result #{i+1}: {result['title']} ({result['href']}) [img:{image_url}]")
    
    # Combine contexts
    doc_context = "\n\n".join([f"Document {i+1} (from {os.path.basename(doc.metadata.get('source', 'unknown'))}, page {doc.metadata.get('page', 'unknown')}):\n{doc.page_content}" for i, doc in enumerate(docs)])
    
    web_context = ""
    if web_results:
        web_context = "\n\n".join([f"Web Result {i+1}:\nTitle: {result['title']}\nContent: {result['body']}\nURL: {result['href']}" for i, result in enumerate(web_results)])
    
    # Create prompt for Azure OpenAI
    prompt = f"""
    Based on the following information, answer this question: {question}
    
    Medical literature:
    {doc_context}
    """
    
    # Add web context if available
    if web_context:
        prompt += f"""
    
    Web search results:
    {web_context}
    """
    
    # Add instructions
    prompt += """
    
    Provide a detailed and accurate answer based on all the information provided. 
    Include citations like [1], [2], etc. when referencing specific information.
    If there are different perspectives or information from different sources, mention them and prioritize the most reliable sources.
    """
    
    # Generate summary using Azure OpenAI
    client = azure_client
    if not client:
        return {"answer": "Error: Azure OpenAI client not available", "sources": citations}
    
    try:
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo")
        
        response = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical assistant specializing in gynecology. Provide clear, accurate information based on medical literature and web search results. Include relevant details and maintain a professional tone. Always include citations to your sources."
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
        
        summary = response.choices[0].message.content
        return {"answer": summary, "sources": citations}
    
    except Exception as e:
        return {"answer": f"Error generating response: {str(e)}", "sources": citations}

@app.route('/')
def index():
    # Add cache control headers to prevent caching
    response = Response(render_template('final.html'))
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

@app.route('/api/ask', methods=['POST'])
def ask():
    data = request.json
    question = data.get('question', '')
    web_search_enabled = True  # Always enabled
    
    if not question:
        return jsonify({"error": "No question provided"}), 400
    
    try:
        # Get relevant documents from FAISS index
        docs = retriever.get_relevant_documents(question)
        
        # Generate answer
        result = generate_answer(question, docs, web_search_enabled)
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Error processing question: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Load FAISS index
    print("Loading FAISS index...")
    retriever = load_faiss_from_blob()
    
    # Create Azure OpenAI client
    print("Creating Azure OpenAI client...")
    azure_client = create_azure_openai_client()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=5000)