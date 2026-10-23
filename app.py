import os
import time
import uuid

import chromadb
import streamlit as st
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer

load_dotenv()

MODELS = ["gemini-2.5-flash", "gemini-3.8-flash", "gemini-3.5-flash"]
RETRY_CODES = (429, 500, 503)
CHUNK_SIZE = 500
OVERLAP = 100
TOP_K = 4
MAX_PAGES = 50

SYSTEM_PROMPT = (
    "You answer questions using ONLY the context provided. "
    "Cite the page number for every fact, like (Page 3). "
    "If the context does not contain the answer, say you could not find it "
    "in the document. Do not use outside knowledge."
)

st.set_page_config(page_title="Document Q&A Assistant")


@st.cache_resource
def load_embedder():
    return SentenceTransformer("all-MiniLM-L6-v2")


@st.cache_resource
def load_client():
    return genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def chunk_text(text):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - OVERLAP
    return chunks


def build_index(uploaded_file):
    reader = PdfReader(uploaded_file)
    documents = []
    ids = []
    metadatas = []
    for i, page in enumerate(reader.pages[:MAX_PAGES]):
        text = page.extract_text() or ""
        for j, chunk in enumerate(chunk_text(text)):
            if chunk.strip() == "":
                continue
            documents.append(chunk)
            ids.append("page" + str(i + 1) + "_chunk" + str(j))
            metadatas.append({"page": i + 1})
    if not documents:
        return None, 0
    embeddings = load_embedder().encode(documents).tolist()
    chroma = chromadb.EphemeralClient()
    collection = chroma.create_collection("docs_" + uuid.uuid4().hex)
    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )
    return collection, len(documents)


def retrieve(collection, question):
    q_emb = load_embedder().encode([question]).tolist()
    results = collection.query(query_embeddings=q_emb, n_results=TOP_K)
    return list(zip(results["documents"][0], results["metadatas"][0]))


def build_context(chunks):
    parts = []
    for doc, meta in chunks:
        parts.append("[Page " + str(meta["page"]) + "]\n" + doc)
    return "\n\n".join(parts)


def generate(prompt):
    client = load_client()
    last_error = None
    for model in MODELS:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=SYSTEM_PROMPT,
                        max_output_tokens=500,
                    ),
                )
                return response.text
            except Exception as e:
                last_error = e
                code = getattr(e, "code", None)
                if code not in RETRY_CODES:
                    raise
                time.sleep(2 * (attempt + 1))
    return "Sorry, the AI service is busy right now. Please try again in a minute. " + str(last_error)[:120]


st.title("Document Q&A Assistant")
st.caption("Upload a PDF, ask questions, and get answers with page citations.")

with st.sidebar:
    st.header("Your document")
    uploaded = st.file_uploader("Upload a PDF", type="pdf")
    st.caption("Only the first " + str(MAX_PAGES) + " pages are used.")

if uploaded is None:
    st.info("Upload a PDF in the sidebar to get started.")
    st.stop()

file_key = uploaded.name + "_" + str(uploaded.size)
if st.session_state.get("file_key") != file_key:
    with st.spinner("Reading and indexing your document..."):
        collection, count = build_index(uploaded)
    st.session_state["file_key"] = file_key
    st.session_state["collection"] = collection
    st.session_state["count"] = count
    st.session_state["messages"] = []

if st.session_state["collection"] is None:
    st.error("No readable text found. This may be a scanned PDF. Try another file.")
    st.stop()

st.sidebar.success("Indexed " + str(st.session_state["count"]) + " chunks.")

for message in st.session_state["messages"]:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("sources"):
            with st.expander("Sources"):
                for page, text in message["sources"]:
                    st.markdown("**Page " + str(page) + "**")
                    st.text(text)

question = st.chat_input("Ask a question about your document")
if question:
    st.session_state["messages"].append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            chunks = retrieve(st.session_state["collection"], question)
            prompt = "Context:\n" + build_context(chunks) + "\n\nQuestion: " + question
            answer = generate(prompt)
        st.markdown(answer)
        sources = [(meta["page"], doc) for doc, meta in chunks]
        with st.expander("Sources"):
            for page, text in sources:
                st.markdown("**Page " + str(page) + "**")
                st.text(text)

    st.session_state["messages"].append(
        {"role": "assistant", "content": answer, "sources": sources}
    )