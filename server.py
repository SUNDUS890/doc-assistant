import os
import time
import uuid

import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from google import genai
from google.genai import types
from pydantic import BaseModel
from pypdf import PdfReader


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

app = FastAPI()
EMBEDDING_MODEL = "gemini-embedding-001"
gemini = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
chroma = chromadb.EphemeralClient()
sessions = {}


class AskRequest(BaseModel):
    session_id: str
    question: str


def chunk_text(text):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + CHUNK_SIZE])
        start += CHUNK_SIZE - OVERLAP
    return chunks


def generate(prompt):
    last_error = None
    for model in MODELS:
        for attempt in range(3):
            try:
                response = gemini.models.generate_content(
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


@app.post("/api/upload")
def upload(file: UploadFile = File(...)):
    reader = PdfReader(file.file)
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
        raise HTTPException(status_code=400, detail="No readable text found. This may be a scanned PDF.")
    result = gemini.models.embed_content(
    model=EMBEDDING_MODEL,
    contents=documents,
    config={"task_type": "RETRIEVAL_DOCUMENT"}
)

    embeddings = [item.values for item in result.embeddings]
    session_id = uuid.uuid4().hex
    collection = chroma.create_collection("docs_" + session_id)
    collection.add(documents=documents, embeddings=embeddings, ids=ids, metadatas=metadatas)
    sessions[session_id] = collection
    return {"session_id": session_id, "chunks": len(documents), "filename": file.filename}


@app.post("/api/ask")
def ask(req: AskRequest):
    collection = sessions.get(req.session_id)
    if collection is None:
        raise HTTPException(status_code=404, detail="Session expired. Please upload the PDF again.")
    q_result = gemini.models.embed_content(
    model=EMBEDDING_MODEL,
    contents=[req.question],
    config={"task_type": "RETRIEVAL_QUERY"}
)

    q_emb = [q_result.embeddings[0].values]
    results = collection.query(query_embeddings=q_emb, n_results=TOP_K)
    chunks = list(zip(results["documents"][0], results["metadatas"][0]))
    context = "\n\n".join("[Page " + str(m["page"]) + "]\n" + d for d, m in chunks)
    answer = generate("Context:\n" + context + "\n\nQuestion: " + req.question)
    sources = [{"page": m["page"], "text": d} for d, m in chunks]
    return {"answer": answer, "sources": sources}


app.mount("/", StaticFiles(directory="web", html=True), name="web")
