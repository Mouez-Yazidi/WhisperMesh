import streamlit as st
from audio_recorder_streamlit import audio_recorder
import base64
import tempfile
from gtts import gTTS
import io
from utils import (document_store_init, 
indexing_pipeline_builder,
retriever_pipeline_builder,
read_pdf,audio_transcriber,
create_chat_message,
auto_play_audio
)

def main():
    # Access secret values
    cohere_api_key = st.secrets["COHERE_API_KEY"]
    groq_api = st.secrets["GROQ_API"]
    groq_key = st.secrets["GROQ_KEY"]
    qdrant_api = st.secrets["QDRANT_API"]
    qdrant_key = st.secrets["QDRANT_KEY"]

    # Store secrets in session_state
    #cohere
    if "cohere_api_key" not in st.session_state:
        st.session_state.cohere_api_key = cohere_api_key
    #groqcloud
    if "groq_api" not in st.session_state:
        st.session_state.groq_api = groq_api
    if "groq_key" not in st.session_state:
        st.session_state.groq_key = groq_key
    #Qdrant
    if "qdrant_api" not in st.session_state:
        st.session_state.qdrant_api = qdrant_api
    if "qdrant_key" not in st.session_state:
        st.session_state.qdrant_key = qdrant_key

    #initialize document store
    document_store = document_store_init(api_key=qdrant_key, url=qdrant_api)

    #retriever_pipeline
    retriever_pipeline = retriever_pipeline_builder(document_store=document_store, 
                                                    cohere_key=st.session_state.cohere_api_key,
                                                    groq_api = st.session_state.groq_api,
                                                    groq_key=st.session_state.groq_key)
    
    with st.sidebar:
        # Toggle pop-up state
        if "show_instructions" not in st.session_state:
            st.session_state.show_instructions = False
        
        # Button to toggle instructions
        if st.button("ℹ️ Show/Hide Instructions"):
            st.session_state.show_instructions = not st.session_state.show_instructions

        if st.session_state.show_instructions:
            st.markdown("""
                <div style="background-color: #f9f9f9; padding: 20px; border-radius: 10px;">
                
                ### 📄 Step 1: Upload your PDF Documents
                - Drag and drop your files or click 'Browse Files' to select them.
                - The maximum file size is 200MB.
                
                ### ⚙️ Step 2: Index your Documents
                - Click the '📄 Index Document' button to start the indexing process.
                - The bot will use these documents to answer your questions.
        
                ### 💬 Step 3: Ask your Questions
                - Use the text box below to type your question. 📝
                - You can also click on the 🎙️ microphone icon to ask questions via voice input.
                </div>
                """, unsafe_allow_html=True)
        st.subheader("Upload your PDF files and start interacting with the chatbot 🤖.")
        st.image('indexing.png')
        uploaded_files = st.file_uploader("### 🗂️ Upload PDF files", type="pdf", accept_multiple_files=True)
        if st.button('📄 Index Documents'):
            if uploaded_files is not None:
                try:
                    # #initialize document store
                    # document_store = document_store_init(api_key=qdrant_key, url=qdrant_api)
                    files_path = []
                    for uploaded_file in uploaded_files:
                        # Save the uploaded PDF temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                            temp_file.write(uploaded_file.read())
                            temp_file_path = temp_file.name
                            files_path.append(temp_file_path)
                    
                    #indexing pipeline 
                    indexing_pipeline = indexing_pipeline_builder(document_store=document_store, cohere_key=st.session_state.cohere_api_key)
                    
                    indexing_pipeline.run({"converter": {"sources": files_path}})
                    st.success('Document indexed, you can start asking questions!', icon="✅")
                    st.session_state.start_chat = True
                except Exception as e:
                    st.warning(f'Failed to index document, please try again \n error:{str(e)}', icon="⚠️")
                    init_vector_db = False
            else:
                st.warning("Please upload the documents and provide the missing fields.", icon="⚠️")
    st.sidebar.markdown("<br><br>", unsafe_allow_html=True)
    st.sidebar.write("📧 [Email us](mailto:mouez.yazidi2016@gmail.com) | 👔 [LinkedIn](https://www.linkedin.com/in/yazidi-mouez-35ba88183/)")
    
    st.title("🎤 RAG Chatbot using Haystack")

    st.subheader("How would you like to chat today? 🗣️🎤 or 💬🖊️")
    option = st.selectbox("",["Text 💬", "Voice 🎤"])

    if option == "Text 💬":
        # Initialize session state for chat history
        if "messages" not in st.session_state:
            st.session_state.messages = [] 


        st.image('https://cdn-icons-gif.flaticon.com/11184/11184177.gif')
        # Display chat messages from history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # React to user input
        if prompt := st.chat_input("What is up?"):
            # Add user message to chat history
            st.session_state.messages.append({"role": "user", "content": prompt})
            # Display user message in chat message container
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # Generate bot response
            response = retriever_pipeline.run({"text_embedder":{"text": prompt}, "prompt_builder": {"question": prompt}})
    
            # Add bot message to chat history
            st.session_state.messages.append({"role": "assistant", "content": response["llm"]["replies"][0]})
            # Display bot message in chat message container
            with st.chat_message("assistant"):
                st.markdown(response["llm"]["replies"][0])
    else:
        st.image('https://cdn.dribbble.com/users/37530/screenshots/2937858/drib_blink_bot.gif')
        recorded_audio = audio_recorder()
        if recorded_audio:
            audio_file = "reocord.mp3"
            with open(audio_file, "wb") as f:
                f.write(recorded_audio)

            # transxribe question from audio to text
            transcribed_text = audio_transcriber(groq_api = st.session_state.groq_api,
                                                 groq_key=st.session_state.groq_key,
                                                 audio_path=audio_file)

            create_chat_message(sender="User", message=transcribed_text, sender_type="user", avatar_url="https://www.svgrepo.com/show/382106/male-avatar-boy-face-man-user-9.svg")
            #Generate bot response
            response = retriever_pipeline.run({"text_embedder":{"text": transcribed_text}, "prompt_builder": {"question": transcribed_text}})
            # Generate the audio from the response text
            response_audio_file = io.BytesIO()
            tts = gTTS(response["llm"]["replies"][0])
            tts.write_to_fp(response_audio_file)
            response_audio_file.seek(0)  # Reset the file pointer
            # Play the audio in Streamlit
            st.audio(response_audio_file)
            create_chat_message(sender="AI Assistant", message=response["llm"]["replies"][0], sender_type="bot", avatar_url="https://cdn-icons-png.flaticon.com/512/8649/8649607.png")

if __name__ == "__main__":
    main()
