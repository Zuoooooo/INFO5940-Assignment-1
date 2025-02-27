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

if "processed_files" not in st.session_state:
    st.session_state["processed_files"] = set() 

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
            if uploaded_file.name in st.session_state["processed_files"]:
                continue  # Skip files already processed

            file_path = os.path.join(UPLOAD_DIR, uploaded_file.name)
            with open(file_path, "wb") as f:
                f.write(uploaded_file.read())

            try:
                # Load files with correct metadata
                if uploaded_file.name.endswith('.pdf'):
                    loader = PDFMinerLoader(file_path)
                else:
                    loader = TextLoader(file_path)

                documents = loader.load()

                # Store correct metadata before processing
                for doc in documents:
                    doc.metadata["source"] = uploaded_file.name 

                # Chunk documents
                text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
                chunks = text_splitter.split_documents(documents)

                # Store chunks into ChromaDB (ensure metadata persists)
                db.add_documents(chunks)

                # Mark file as processed
                st.session_state["processed_files"].add(uploaded_file.name)

            except ValueError as e:
                st.error(f"Error processing file {uploaded_file.name}: {str(e)}")

        st.success("Documents uploaded and processed successfully!")

    # Chat functionality
    if prompt := st.chat_input("Ask a question"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        retriever = db.as_retriever(search_type="similarity", search_kwargs={"k": 5})
        docs = retriever.invoke(prompt)

        for doc in docs:
            print(f"Retrieved from: {doc.metadata.get('source', 'Unknown')}\nContent: {doc.page_content[:300]}")

        # Prepare context (without inline source mention)
        context = "\n\n".join([doc.page_content for doc in docs])

        # Select all unique sources used in retrieval
        sources = list(set(doc.metadata.get('source', 'Unknown') for doc in docs))
        source_display = ", ".join(sources) if sources else "Unknown Source"

        # Generate response
        chat = ChatOpenAI(model="openai.gpt-4o", temperature=0, api_key=OPENAI_API_KEY)

        system_prompt = SystemMessage(
            content="You are an assistant for question-answering tasks. Use the following retrieved context to answer the question.  If you don't know the answer, just say that you don't know. "
        )

        user_message = HumanMessage(content=f"Context: {context}\n\nQuestion: {prompt}")

        response = chat.invoke([system_prompt, user_message])  

        # Stream response
        with st.chat_message("assistant"):
            st.write(response.content)
            st.caption(f"Sources: {source_display}") 

        st.session_state.messages.append({"role": "assistant", "content": response.content + f"\n\n(Sources: {source_display})"})
