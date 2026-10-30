import os
from dotenv import load_dotenv

from langchain_community.document_loaders import UnstructuredPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_groq import ChatGroq
from langchain_classic.chains import RetrievalQA

# Load environment variables from .env file
load_dotenv()

working_dir = os.path.dirname(os.path.abspath((__file__)))

# Load the embedding model
embedding =HuggingFaceEmbeddings()

# Load the Llama model from groq
llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
)

def process_document_to_chroma_db(file_name):
    # Load the pdf document using UnstructuredPdfLoader
    loader = UnstructuredPDFLoader(f"{working_dir}/{file_name}")
    documents = loader.load()
    # split the text into chunks for embedding
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 2000,
        chunk_overlap = 200
    )
    texts = text_splitter.split_documents(documents)
    # store the document chunks in a chroma vector database
    vectordb = Chroma.from_documents(
        documents=texts,
        embedding=embedding,
        persist_directory=f"{working_dir}/doc_vectorstore"
    )
    return 0

def answer_question(user_question):
    # Load the persistant chroma vector database
    vectordb = Chroma(
        persist_directory=f"{working_dir}/doc_vectorstore",
        embedding_function=embedding
    )


    # create a retriever for document search
    retriever = vectordb.as_retriever()

    # create a RetrievalQA chain to answer userquestion using Llama-3.3-70B

    qa_chain = RetrievalQA.from_chain_type(
        llm = llm,
        chain_type = "stuff",
        retriever = retriever,
    )
    response = qa_chain.invoke({"query":user_question})
    answer =response["result"]

    return answer