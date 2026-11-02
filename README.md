# 🚀 DocMind AI – Intelligent Document Question Answering System

An AI-powered document assistant built using Retrieval-Augmented Generation (RAG). Upload PDF documents, ask questions, and receive intelligent, context-aware answers with source references.

## 🌟 Overview

DocMind AI simplifies the process of understanding large PDF documents. Instead of manually searching through pages, users can upload documents and interact with their content using natural language.

The application uses RAG architecture to retrieve relevant information from uploaded documents and generate accurate responses using a Large Language Model (LLM).

## ✨ Key Features

* 📄 PDF document uploading and text extraction.
* ✂️ Intelligent text chunking.
* 🧠 Semantic search using vector embeddings.
* 🗄️ Vector storage and retrieval using ChromaDB.
* 🤖 AI-powered question answering.
* 📌 Context-based answers with source references.
* 💬 Interactive user interface.

## 🛠️ Technologies Used

| Technology            | Purpose                        |
| --------------------- | ------------------------------ |
| Python                | Core programming language      |
| Streamlit             | User interface                 |
| Google Gemini API     | Large Language Model           |
| Sentence Transformers | Text embeddings                |
| ChromaDB              | Vector database                |
| PyPDF                 | PDF text extraction            |
| RAG                   | Retrieval-Augmented Generation |

## ⚙️ How It Works

1. **Document Upload:** Users upload PDF documents.
2. **Text Extraction:** Text is extracted from the uploaded PDFs.
3. **Chunking:** Extracted text is divided into smaller chunks.
4. **Embedding Generation:** Text chunks are converted into vector embeddings.
5. **Vector Storage:** Embeddings are stored in ChromaDB.
6. **Semantic Retrieval:** Relevant chunks are retrieved based on the user's question.
7. **Answer Generation:** Gemini generates an answer using the retrieved context.
8. **Source References:** Relevant document references are provided with the answer.

## 🏗️ Project Architecture

PDF Upload → Text Extraction → Text Chunking → Embeddings → ChromaDB → Semantic Retrieval → Gemini LLM → Answer with Sources

## 💻 Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/SUNDUS890/doc-assistant.git
```

### 2. Navigate to the project directory

```bash
cd doc-assistant
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API credentials

Add your Gemini API key using the environment variable or configuration method required by your application.

Never upload API keys or secrets to GitHub.

### 5. Run the application

Use the appropriate command for your project entry-point file. For example:

```bash
streamlit run app.py
```

## 🎯 Project Objective

The main objective of DocMind AI is to make document interaction faster and easier through Generative AI and Retrieval-Augmented Generation.

## 👩‍💻 Developer

**Sundus Nasar**

B.Tech Data Science Student | AI & ML Enthusiast

GitHub: [SUNDUS890](https://github.com/SUNDUS890)

LinkedIn: [Sundus Nasar](https://www.linkedin.com/in/sundus-nasar/)

---

⭐ If you find this project interesting, feel free to explore the repository!
