from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

from app.core.config import settings


def chunk_text(text: str) -> list[str]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
    )
    return splitter.split_text(text)


def create_vectorstore(file_id: str, chunks: list[str]) -> Chroma:
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
    )
    vectorstore = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=f"{settings.VECTORSTORE_DIR}/{file_id}",
        collection_name=file_id,
    )
    return vectorstore


def load_vectorstore(file_id: str) -> Chroma:
    embeddings = OpenAIEmbeddings(
        model=settings.EMBEDDING_MODEL,
        openai_api_key=settings.OPENAI_API_KEY,
    )
    return Chroma(
        persist_directory=f"{settings.VECTORSTORE_DIR}/{file_id}",
        embedding_function=embeddings,
        collection_name=file_id,
    )
