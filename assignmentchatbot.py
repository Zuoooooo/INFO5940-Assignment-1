import streamlit as st
from openai import OpenAI
from langchain_community.document_loaders import TextLoader, PDFMinerLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from os import environ
import os

# Streamlit UI
st.title("RAG Chatbot")
st.caption("Powered by INFO-5940")

if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "Hello! Upload a document or ask me a question."}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Ensure API key is correctly set
OPENAI_API_KEY = environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    st.error("Missing OpenAI API Key. Please set the OPENAI_API_KEY environment variable.")
else:
    embeddings = OpenAIEmbeddings(model="openai.text-embedding-3-large", api_key=OPENAI_API_KEY)

    # Initialize ChromaDB
    vector_store_path = "./chroma_db"
    db = Chroma(embedding_function=embeddings, persist_directory=vector_store_path)

    UPLOAD_DIR = "uploaded_docs"
    os.makedirs(UPLOAD_DIR, exist_ok=True)

    # Upload documents
    uploaded_files = st.file_uploader("Upload .txt or .pdf files", accept_multiple_files=True)

    if uploaded_files:
        for uploaded_file in uploaded_files:
            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            try:
                # Load files
                if uploaded_file.name.endswith('.pdf'):
                    loader = PDFMinerLoader(file_path)
                else:
                    loader = TextLoader(file_path)

                documents = loader.load()

                # Text chunking
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
                chunks = text_splitter.split_documents(documents)
                
                # Store in ChromaDB
                db.add_documents(chunks)

            except ValueError as e:
                st.error(f"Error processing file {uploaded_file.name}: {str(e)}")

        st.success("Documents uploaded and processed successfully!")

    # Chat functionality
    if prompt := st.chat_input("Ask a question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        # Retrieve relevant documents
        retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 2})
        docs = retriever.invoke(prompt) 

        context = "\n\n".join([doc.page_content for doc in docs])

        # Generate response
        chat = ChatOpenAI(model="openai.gpt-4o", temperature=0.2, api_key=OPENAI_API_KEY)

        system_prompt = SystemMessage(
            content="You are a question-answering assistant. Use the retrieved documents to answer the question. "
                    "Do not make up information. Answer in no more than three sentences, be concise."
        )

        user_message = HumanMessage(content=f"Context: {context}\n\nQuestion: {prompt}")

        response = chat.invoke([system_prompt, user_message])  

        # Stream response
        with st.chat_message("assistant"):
            st.write(response.content)

        st.session_state.messages.append({"role": "assistant", "content": response.content})
