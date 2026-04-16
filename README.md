# 🏗️ ArchPlan: AI-Powered System Architect

ArchPlan is an **iterative** architecture design assistant that generates system blueprints from natural language requirements. It combines:

* a deterministic constraint extractor,
* retrieval-augmented prompt enrichment,
* multi-provider LLM orchestration,
* live Mermaid diagram rendering,
* and a frontend refinement loop.

---

## 🌟 Key Features

* **Structured constraint extraction:** Reads the user's request and extracts budget, peak RPS, region, cloud provider, stack preferences, compliance rules, and more.
* **Iterative refinement:** Supports a design update workflow where the current diagram and component set are sent back to the model for surgical changes.
* **RAG-powered guidance:** Uses a local ChromaDB knowledge store and `SentenceTransformer` embeddings to surface relevant architecture patterns.
* **Provider-flexible inference:** Generates designs with Google Gemini by default and falls back to local Ollama if needed.
* **Live Mermaid visualization:** Renders the LLM's single-line Mermaid graph in the browser and preserves state in `localStorage`.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, Tailwind CSS, JavaScript (ES6+), Mermaid.js |
| **Backend** | FastAPI, Pydantic, Python 3.10+ |
| **LLM Providers** | Google Gemini, Ollama (`qwen2.5-coder:7b-instruct-q4_0`) |
| **RAG Search** | ChromaDB + `sentence-transformers` |
| **Constraint extraction** | deterministic JSON prompt + Ollama zero-temperature inference |

---

## 🚀 Getting Started

### 1. Prerequisites
* Python 3.10+ installed.
* [Ollama](https://ollama.ai/) installed and running locally.
* Optional: `GOOGLE_API_KEY` if you want to use Google Gemini as the first provider.

### 2. Prepare the LLM
```bash
ollama pull qwen2.5-coder:7b-instruct-q4_0
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Start the API
```bash
uvicorn app.main:app --reload --port 8000
```

### 5. Open the Frontend
Open `index.html` in your browser, or serve the root directory with a static file server.

---

## 🧠 How it Works

1. **User request** is entered in the browser, then posted to `/generate`.
2. **Constraint extraction** runs via `backend/app/services/constraint_extractor.py`, which uses local Ollama at zero temperature to return clean JSON.
3. **RAG retrieval** uses `backend/app/rag/retriever.py` and `backend/app/rag/chroma_client.py` to fetch top documents from ChromaDB.
4. **Prompt assembly** happens in `backend/app/services/prompts.py`, with strict JSON-only instructions for both initial design and refinement.
5. **LLM generation** runs through `backend/app/services/llm_service.py`, selecting Gemini or Ollama and sanitizing the model output into the frontend schema.
6. **Frontend rendering** stores diagram and component state in `localStorage` and renders the Mermaid architecture graph.

---

## 📂 Project Structure

```text
ArchPlan/
├── backend/
│   ├── app/
│   │   ├── models/           # Pydantic request/response schemas
│   │   ├── rag/              # ChromaDB client and retrieval logic
│   │   ├── routes/           # FastAPI route definitions
│   │   ├── services/         # constraint extraction and LLM orchestration
│   │   └── prompts.py        # system and refinement prompt templates
│   ├── chroma_db/            # local ChromaDB data store
│   ├── requirements.txt      # Python dependencies
│   └── run.py                # optional app runner
├── data/                     # example data and knowledge sources
├── frontend/                 # static UI files
│   ├── index.html
│   └── script.js
└── README.md
```

---

## ⚠️ Notes

* The frontend can choose between `gemini` and `ollama` via provider selection.
* The refine path sends `existing_diagram`, `existing_components`, and `cached_constraints` back to the backend.
* If Gemini fails, the backend automatically falls back to local Ollama.

---

## ⚖️ License
MIT License
