import chromadb
from sentence_transformers import SentenceTransformer

model = SentenceTransformer("all-MiniLM-L6-v2")
client = chromadb.PersistentClient(path="chroma_db")
collection = client.get_collection("docs")

question = input("Ask a question: ")
q_embedding = model.encode([question]).tolist()
results = collection.query(query_embeddings=q_embedding, n_results=3)

for doc, meta in zip(results["documents"][0], results["metadatas"][0]):
    print("\n--- Page", meta["page"], "---")
    print(doc)