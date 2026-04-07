# 🏗️ ArchPlan: AI-Powered System Architect

ArchPlan is an **iterative** system design generator that utilizes **Retrieval-Augmented Generation (RAG)** and a **Deterministic Extraction Layer** to provide production-grade architecture blueprints. Unlike generic LLMs, ArchPlan consults internal knowledge bases and maintains session state to allow for continuous design refinement.

---

## 🌟 Key Features

* **Multi-Stage Extraction:** Uses a zero-temperature "Constraint Engine" to pull technical requirements (Budget, RPS, Region, Stack) into a structured JSON schema.
* **Iterative Refinement:** Supports a "Refine Design" loop where the architect modifies existing diagrams based on conversational feedback.
* **RAG Enrichment:** Queries a local **ChromaDB** vector store to inject "gold-standard" patterns into the LLM prompt.
* **Visual Logic:** Generates live, interactive system diagrams using **Mermaid.js** with unique render-ID management.
* **GPU Optimized:** Tuned for high-precision technical reasoning using **Qwen 2.5 Coder** on consumer-grade hardware (e.g., RTX 2050).

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, Tailwind CSS, JavaScript (ES6+), Mermaid.js |
| **Backend** | FastAPI (Python 3.10+) |
| **LLM Engine** | Ollama (Model: `qwen2.5-coder:7b`) |
| **Vector DB** | ChromaDB (for RAG) |
| **Parsing** | Deterministic Regex & JSON Sanitizers |

---

## 🚀 Getting Started

### 1. Prerequisites
* [Ollama](https://ollama.ai/) installed and running.
* Python 3.10+ installed.

### 2. Prepare the LLM
```bash
ollama pull qwen2.5-coder:7b-instruct-q4_0
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the Servers
```bash
# Start FastAPI (from /backend)
uvicorn main:app --reload --port 8000
```

---

## 🧠 How it Works (The Pipeline)



1.  **Extraction:** The system passes the query through a **Classifier** to extract constraints (Budget, Region, Scale).
2.  **Retrieval:** ChromaDB fetches the top 3 relevant architectural patterns based on the use case.
3.  **Inference:** The LLM receives the Query + Constraints + RAG Context + Existing Diagram (if refining).
4.  **Sanitization:** Python layers clean the output, validate Mermaid syntax, and standardize component categories.
5.  **Rendering:** The UI updates narratives and diagrams without a page refresh using unique `Date.now()` seeds.

---

## 📂 Project Structure

```text
ArchPlan/
├── backend/
│   ├── app/
│   │   ├── models/       # Pydantic Schemas
│   │   ├── rag/          # ChromaDB & Retriever logic
│   │   ├── services/     # extractor.py & llm_service.py
│   │   └── prompts.py    # Dynamic System Prompts
│   └── main.py           # FastAPI Entry point
├── data/                 # Knowledge base docs (.txt/.pdf)
├── index.html            # UI Layer
└── script.js             # State & Async Fetch logic
```

---

## ⚖️ License
MIT License