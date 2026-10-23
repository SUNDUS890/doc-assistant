import os
import time
import chromadb
from dotenv import load_dotenv
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

load_dotenv()

MODELS = ["gemini-2.5-flash", "gemini-3.8-flash", "gemini-3.5-flash"]
RETRY_CODES = (429, 500, 503)
TOP_K = 4

embedder = SentenceTransformer("all-MiniLM-L6-v2")
db = chromadb.PersistentClient(path="chroma_db")
collection = db.get_collection("docs")
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

SYSTEM_PROMPT = (
    "You answer questions using ONLY the context provided. "
    "Cite the page number for every fact, like (Page 3). "
    "If the context does not contain the answer, say you could not find it "
    "in the document. Do not use outside knowledge."
)


def retrieve(question):
    q_emb = embedder.encode([question]).tolist()
    results = collection.query(query_embeddings=q_emb, n_results=TOP_K)
    return list(zip(results["documents"][0], results["metadatas"][0]))


def build_context(chunks):
    parts = []
    for doc, meta in chunks:
        parts.append("[Page " + str(meta["page"]) + "]\n" + doc)
    return "\n\n".join(parts)


def generate(prompt):
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
                print("(" + model + " busy, retrying...)")
                time.sleep(2 * (attempt + 1))
    return "Sorry, the AI service is busy right now. Please try again in a minute. " + str(last_error)[:120]


def ask(question):
    chunks = retrieve(question)
    context = build_context(chunks)
    prompt = "Context:\n" + context + "\n\nQuestion: " + question
    return generate(prompt)


if __name__ == "__main__":
    while True:
        q = input("\nAsk a question (or type quit): ")
        if q.strip().lower() == "quit":
            break
        print("\n" + ask(q))