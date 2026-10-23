from pypdf import PdfReader
import chromadb
from sentence_transformers import SentenceTransformer

PDF_PATH = "data/sample.pdf"
CHUNK_SIZE = 500
OVERLAP = 100


def load_pages(path):
    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append((i + 1, text))
    return pages


def chunk_text(text, size, overlap):
    chunks = []
    start = 0
    while start < len(text):
        chunks.append(text[start:start + size])
        start += size - overlap
    return chunks


def main():
    pages = load_pages(PDF_PATH)

    documents = []
    ids = []
    metadatas = []
    for page_num, text in pages:
        for j, chunk in enumerate(chunk_text(text, CHUNK_SIZE, OVERLAP)):
            if chunk.strip() == "":
                continue
            documents.append(chunk)
            ids.append(f"page{page_num}_chunk{j}")
            metadatas.append({"page": page_num, "source": PDF_PATH})

    print("Total chunks:", len(documents))

    print("Loading embedding model (first time downloads it)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(documents).tolist()

    client = chromadb.PersistentClient(path="chroma_db")
    try:
        client.delete_collection("docs")
    except Exception:
        pass
    collection = client.create_collection("docs")
    collection.add(
        documents=documents,
        embeddings=embeddings,
        ids=ids,
        metadatas=metadatas,
    )
    print("Done. Stored", collection.count(), "chunks in the database.")


if __name__ == "__main__":
    main()