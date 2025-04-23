from pathlib import Path
import tempfile
from haystack import Pipeline
from haystack.components.converters import PyPDFToDocument
from haystack.components.preprocessors import DocumentCleaner, DocumentSplitter
from haystack.components.writers import DocumentWriter
from haystack.document_stores.types import DuplicatePolicy
from haystack_integrations.components.embedders.cohere.text_embedder import CohereTextEmbedder
from haystack_integrations.components.embedders.cohere.document_embedder import CohereDocumentEmbedder
from haystack.utils import Secret
from haystack_integrations.components.retrievers.qdrant import QdrantEmbeddingRetriever
from haystack_integrations.document_stores.qdrant import QdrantDocumentStore
from haystack.components.generators import OpenAIGenerator
from haystack.components.builders import PromptBuilder
from haystack.components.audio import RemoteWhisperTranscriber
import streamlit as st
import base64


def document_store_init(api_key:str ,url:str , index_name='RAG') -> QdrantDocumentStore:
    # Initialize document store
    document_store = QdrantDocumentStore(
        api_key=Secret.from_token(api_key),
        url=url,
        recreate_index=False,
        return_embedding=True,
        wait_result_from_api=True,
        embedding_dim=1024,
        index=index_name,
        similarity="cosine"
    )
    return document_store

def indexing_pipeline_builder(document_store: QdrantDocumentStore, cohere_key) -> Pipeline:

    # Add components to the indexing pipeline
    ## Create pipeline components
    converter = PyPDFToDocument()
    cleaner = DocumentCleaner()
    splitter = DocumentSplitter(split_by="sentence", split_length=10, split_overlap=2)
    embedder = CohereDocumentEmbedder(api_key=Secret.from_token(cohere_key),model="embed-multilingual-v3.0")
    writer = DocumentWriter(document_store=document_store, policy=DuplicatePolicy.SKIP)

    # Add components to the indexing pipeline
    indexing_pipeline = Pipeline()
    indexing_pipeline.add_component("converter", converter)
    indexing_pipeline.add_component("cleaner", cleaner)
    indexing_pipeline.add_component("splitter", splitter)
    indexing_pipeline.add_component("embedder", embedder )
    indexing_pipeline.add_component("writer", writer)

    # Connect the components to each other
    indexing_pipeline.connect("converter", "cleaner")
    indexing_pipeline.connect("cleaner", "splitter")
    indexing_pipeline.connect("splitter", "embedder")
    indexing_pipeline.connect("embedder", "writer")
    return indexing_pipeline

def retriever_pipeline_builder(document_store:QdrantDocumentStore, cohere_key:str, groq_api:str, groq_key:str) -> Pipeline:

    llm = OpenAIGenerator(
        api_key=Secret.from_token(groq_key),
        api_base_url=groq_api,
        model="deepseek-r1-distill-llama-70b",
        generation_kwargs = {"max_tokens": 4096,
                            "temperature": 0}
    )

    template = """
    Role:
        You are an AI designed to answer questions strictly based on the information contained in the provided documents. \
        Your task is to analyze the available content and generate a relevant response.

    Guidelines:
        * Greetings: If the input is a greeting, respond with a brief, friendly message, such as: "Hello! How can I assist you today?"
        * No Documents Available: If no documents are provided or they are empty, respond with: "I don't have the necessary information to answer your question."
        * Token Limit for Greetings/No Documents/ general question: Keep your response under 30 tokens if no documents are available or if the input is a greeting or the question is not explicitly covered by the documents.
        * Document-Based Answers: For questions, base your response only on the content from the provided documents. Avoid using any external knowledge. If the question is not explicitly covered by the documents, respond with: "I don't have the information."
        * Insufficient Information: If the documents don't contain the necessary information to answer the question, respond with: "I don't have the information."

    Example Scenarios:
        * Greeting Example:
            Input: "Hi there!"
            Output: "Hello! How can I assist you today?"
        * No Documents Example:
            Input: "What is the capital of France?"
            Output: "I don't have the necessary information to answer your question."
        * Document-Based Answer Example:
            Input: "What is the main ingredient in a Caesar salad?"
            Output: (Based on the content of the provided documents)
        * General Question Example:
            Input: "What is the difference between euro and dollar?"
            Output: "I don't have the information."

    Important Notes:
        * Ensure that all responses are accurate and relevant to the content provided in the documents.
        * Do not use any external knowledge unless explicitly stated in the provided documents.
        * If multiple documents are provided, loop through them to formulate the answer based on the combined content.

    \nDocuments:
    {% for document in documents %}
        {{ document.content }}
    {% endfor %}
    
    \nQuestion: {{ question }}?
    """

    prompt_builder = PromptBuilder(template=template)
    embedder = CohereTextEmbedder(api_key=Secret.from_token(cohere_key),model="embed-multilingual-v3.0")
    retriever = QdrantEmbeddingRetriever(document_store=document_store)
    # Add components to the RAG pipeline
    rag_pipeline = Pipeline()
    rag_pipeline.add_component("text_embedder", embedder)
    rag_pipeline.add_component("retriever", retriever)
    rag_pipeline.add_component("prompt_builder", prompt_builder)
    rag_pipeline.add_component("llm", llm)
    ## Connect the components to each other
    rag_pipeline.connect("text_embedder.embedding", "retriever.query_embedding")
    rag_pipeline.connect("retriever", "prompt_builder.documents")
    rag_pipeline.connect("prompt_builder", "llm")

    return rag_pipeline

def read_pdf(uploaded_file):
    # Reading the uploaded file as bytes
    return uploaded_file.read()

def audio_transcriber(groq_api, groq_key, audio_path):
    
    whisper = RemoteWhisperTranscriber(api_base_url=groq_api,
                                   api_key=Secret.from_token(groq_key),
                                   model="whisper-large-v3")

    transcription = whisper.run(sources=[audio_path])
    return transcription['documents'][0].content

def parse_structured_message(message):

    lines = message.split("\n")
    html_content = ""
    in_code_block = False

    for line in lines:
        # Handle headings (e.g., "# Heading")
        if line.startswith("# "):
            html_content += f"<h3>{line[2:].strip()}</h3>\n"
        
        # Handle bullet points (e.g., "- Item")
        elif line.startswith("- "):
            if not html_content.endswith("<ul>\n"):
                html_content += "<ul>\n"  # Start unordered list
            html_content += f"<li>{line[2:].strip()}</li>\n"
        
        # Handle code blocks (e.g., text wrapped with triple backticks)
        elif line.startswith("```"):
            if in_code_block:
                html_content += "</code></pre>\n"  # Close code block
                in_code_block = False
            else:
                html_content += "<pre><code>\n"  # Start code block
                in_code_block = True
        
        # Handle regular paragraphs
        else:
            if not in_code_block:
                html_content += f"<p>{line.strip()}</p>\n"
    
    if html_content.endswith("<ul>\n"):
        html_content += "</ul>\n"  # Close unordered list if any
    
    return html_content

def create_chat_message(sender, message, sender_type="user", avatar_url=None):

    # Define different styles for user and bot messages
    background_color = "#e0f7fa" if sender_type == "user" else "#f0f0f5"
    text_color = "#00796b" if sender_type == "user" else "#000"
    alignment = "flex-start" if sender_type == "user" else "flex-end"
    
    # CSS for the message card
    card_style = f"""
    <style>
        .chat-container {{
            display: flex;
            align-items: flex-start;
            justify-content: {alignment};
            margin: 10px 0;
        }}
        .chat-avatar {{
            width: 40px;
            height: 40px;
            border-radius: 50%;
            margin-right: 10px;
        }}
        .chat-message {{
            background-color: {background_color};
            color: {text_color};
            padding: 10px;
            border-radius: 10px;
            max-width: 70%;
            box-shadow: 0px 4px 8px rgba(0, 0, 0, 0.1);
            font-family: 'Arial', sans-serif;
        }}
        .chat-message p {{
            margin: 0;
        }}
    </style>
    """
    # Parse the structured message and convert it into HTML
    parsed_message = parse_structured_message(message)

    # HTML for the message card
    avatar_html = f'<img src="{avatar_url}" class="chat-avatar">' if avatar_url else ''
    
    message_html = f"""
    {card_style}
    <div class="chat-container">
        {avatar_html}
        <div class="chat-message">
            <p><strong>{sender}:</strong></p>
            <p>{parsed_message}</p>
        </div>
    </div>
    """
    
    # Render the message in Streamlit
    st.html(message_html)

def auto_play_audio(audio_file):
    # with open(audio_file, "rb") as audio_file:
    #     audio_bytes = audio_file.read()
    base64_audio = base64.b64encode(audio_file).decode("utf-8")
    audio_html = f'<audio src="data:audio/mp3;base64,{base64_audio}" controls autoplay>'
    st.markdown(audio_html, unsafe_allow_html = True)
