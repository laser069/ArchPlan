# 🏗️ ArchPlan: AI-Powered System Architect

ArchPlan is an intelligent system design generator that uses **Retrieval-Augmented Generation (RAG)** to provide production-grade architecture blueprints. Unlike generic LLMs, ArchPlan consults internal knowledge bases to ensure designs are cost-effective, compliant, and technically sound.

---

## 🌟 Key Features

* **Constraint Extraction:** Automatically identifies budget, scale, region, and tech stack from natural language queries.
* **RAG Enrichment:** Queries a local **ChromaDB** vector store to inject "gold-standard" architecture patterns into the LLM prompt.
* **Ollama Integration:** Powered by **Qwen 2.5 Coder** for high-precision technical reasoning.
* **Visual Diagrams:** Generates live, interactive system diagrams using **Mermaid.js**.
* **Budget-Aware:** Adjusts component selection based on specified monthly USD limits.

---

## 🛠️ Tech Stack

| Layer | Technology |
| :--- | :--- |
| **Frontend** | HTML5, Tailwind CSS, JavaScript (ES6+) |
| **Backend** | FastAPI (Python 3.10+) |
| **LLM Engine** | Ollama (Model: `qwen2.5-coder:7b`) |
| **Vector DB** | ChromaDB (for RAG) |
| **Visualization** | Mermaid.js |

---

## 🚀 Getting Started

### 1. Prerequisites
* [Ollama](https://ollama.ai/) installed and running.
* Python 3.10+ installed.

### 2. Prepare the LLM
Download the specialized coder model:
```bash
ollama pull qwen2.5-coder:7b-instruct-q4_0
```

### 3. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Run the Servers
**Start Ollama:**
```bash
ollama serve
```

**Start FastAPI:**
```bash
# From the /backend directory
uvicorn app.main:app --reload
```

### 5. Launch Frontend
Open `index.html` in your browser (use VS Code **Live Server** for the best experience).

---

## 🧠 How it Works (The Pipeline)

1.  **User Input:** "Design a real-time EdTech app for India with a $1k budget."
2.  **Extraction:** The LLM extracts `{ "region": "ap-south-1", "budget": 1000, "scale": "growth" }`.
3.  **Retrieval:** ChromaDB finds the 3 most relevant "Architecture Best Practices" documents.
4.  **Inference:** The LLM combines the query, the constraints, and the RAG context into a final system design.
5.  **Rendering:** The frontend parses the JSON to display a component list, a strategy narrative, and a Mermaid diagram.

---

## 📂 Project Structure

```text
ArchPlan/
├── backend/
│   ├── app/
│   │   ├── models/       # Pydantic Schemas
│   │   ├── rag/          # ChromaDB & Retriever logic
│   │   ├── routes/       # FastAPI Endpoints
│   │   └── services/     # LLM & Constraint logic
│   └── main.py           # Entry point
├── data/                 # Knowledge base docs (.txt/.pdf)
└── index.html            # UI Layer
```

---

## ⚖️ License
MIT License - Feel free to use this for your own architectural explorations!