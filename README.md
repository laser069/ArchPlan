# 🏗️ ArchPlan: AI-Powered System Architect

ArchPlan is an **intelligent architecture design assistant** that generates comprehensive system blueprints from natural language requirements. It leverages advanced AI techniques including Retrieval-Augmented Generation (RAG), multi-provider LLM orchestration, and interactive visualization to create production-ready system architectures.

## ✨ Key Features

* **🧠 Intelligent Constraint Extraction**: Automatically parses user requirements to extract technical constraints, budget limits, performance requirements, compliance needs, and architectural preferences
* **🔄 Iterative Design Refinement**: Supports collaborative design workflows where users can iteratively refine architectures with AI-powered suggestions
* **📚 RAG-Powered Knowledge Base**: Integrates a local vector database with PDF document ingestion for context-aware architecture recommendations
* **🤖 Multi-Provider LLM Support**: Seamlessly switches between Google Gemini, Groq, OpenRouter, and local Ollama models for maximum reliability
* **📊 Interactive ReactFlow Diagrams**: Real-time rendering of architecture diagrams with drag-and-drop nodes, layered visualization, and interactive components
* **📄 PDF Document Ingestion**: Automatically processes and indexes technical documentation for enhanced design guidance

---

## 🛠️ Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Frontend** | Next.js 14, TypeScript, Tailwind CSS | Modern React framework with type safety |
| **Backend** | FastAPI, Python 3.10+, Pydantic | High-performance async API framework |
| **Database** | ChromaDB | Vector database for document embeddings |
| **LLM Providers** | Google Gemini, Groq, OpenRouter, Ollama | Multi-provider AI model support |
| **Embeddings** | Sentence Transformers | Text vectorization for RAG |
| **Visualization** | ReactFlow | Interactive architecture diagram rendering |
| **PDF Processing** | PyMuPDF (Fitz) | Document ingestion and text extraction |

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+** installed
- **Node.js 18+** installed
- **Ollama** installed and running locally
- **pnpm** package manager (or npm/yarn)

### 1. Clone and Setup
```bash
git clone https://github.com/laser069/ArchPlan.git
cd ArchPlan
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
# source venv/bin/activate

pip install -r requirements.txt
```

### 3. LLM Setup
```bash
# Pull the required Ollama model
ollama pull qwen2.5-coder:7b-instruct-q4_0

# Optional: Set up API keys in backend/.env
# GOOGLE_API_KEY=your_gemini_key
# OPENROUTER_API_KEY=your_openrouter_key
```

### 4. Frontend Setup
```bash
cd ../frontend
pnpm install
pnpm dev
```

### 5. Ingest Knowledge Base (Optional)
```bash
cd ../backend
python -m app.rag.ingest
```

### 6. Start Backend
```bash
# From backend directory
uvicorn app.main:app --reload --port 8000
```

**Access the application:**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs

---

## 🧠 Architecture & Workflow

### System Flow
1. **User Input** → Natural language requirements submitted via Next.js frontend
2. **Constraint Extraction** → Deterministic parsing using zero-temperature Ollama inference
3. **Knowledge Retrieval** → RAG system queries ChromaDB for relevant architectural patterns
4. **AI Generation** → Multi-provider LLM orchestration (Gemini → Groq → OpenRouter → Ollama fallback)
5. **Architecture Synthesis** → Structured JSON output with ReactFlow nodes/edges and component specifications
6. **Interactive Refinement** → Users can drag-and-drop, modify, and iteratively refine designs with AI assistance

### RAG Pipeline
- **Document Ingestion**: PDF files processed and chunked with overlap
- **Vector Embeddings**: Sentence Transformers create semantic representations
- **Similarity Search**: Cosine similarity matching for context retrieval
- **Prompt Enrichment**: Retrieved knowledge injected into LLM prompts

### Multi-Provider LLM Strategy
- **Primary**: Google Gemini (fast, high-quality)
- **Secondary**: Groq (ultra-fast inference, cost-effective)
- **Tertiary**: OpenRouter (broad model selection)
- **Fallback**: Local Ollama (privacy, offline capability)

---

## 📁 Project Structure

```
ArchPlan/
├── backend/                          # FastAPI Backend
│   ├── app/
│   │   ├── core/                     # Configuration & settings
│   │   ├── models/                   # Pydantic schemas
│   │   ├── rag/                      # RAG implementation
│   │   │   ├── chroma_client.py      # Vector DB client
│   │   │   ├── ingest.py            # PDF processing pipeline
│   │   │   ├── retriever.py         # Similarity search
│   │   │   └── test_retriever.py    # RAG testing utilities
│   │   ├── routes/                   # API endpoints
│   │   ├── services/                 # Business logic
│   │   │   ├── constraint_extractor.py
│   │   │   ├── llm_service.py       # Multi-provider orchestration
│   │   │   └── prompts.py           # System prompts
│   │   └── main.py                  # FastAPI application
│   ├── chroma_db/                   # Vector database storage
│   ├── data/                        # Training data & examples
│   ├── docs/                        # PDF knowledge base
│   └── requirements.txt             # Python dependencies
│
├── frontend/                         # Next.js Frontend
│   ├── app/                          # Next.js 14 app directory
│   │   ├── api/                      # API routes
│   │   ├── globals.css               # Global styles
│   │   ├── layout.tsx               # Root layout
│   │   └── page.tsx                 # Main page
│   ├── components/                   # React components
│   │   ├── Canvas.tsx               # Architecture diagram
│   │   └── Editor.tsx               # Design interface
│   ├── hooks/                       # Custom React hooks
│   ├── lib/                         # Utility functions
│   └── public/                      # Static assets
│
├── .gitignore                       # Git ignore rules
└── README.md                        # This file
```

---

## 🔧 Configuration

### Environment Variables
Create `backend/.env`:
```env
# LLM API Keys (optional - falls back to Ollama)
GOOGLE_API_KEY=your_gemini_api_key
OPENROUTER_API_KEY=your_openrouter_key

# Application Settings
DEBUG=true
PORT=8000
```

### Knowledge Base Setup
1. Place PDF documents in `backend/docs/`
2. Run ingestion: `python -m app.rag.ingest`
3. Documents are automatically chunked and indexed

---

## 🧪 Development

### Running Tests
```bash
# Backend tests
cd backend
python -m pytest

# RAG system tests
python test_retriever.py
```

### API Testing
```bash
# Test constraint extraction
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a scalable e-commerce platform", "provider": "groq"}'

# Test with specific model
curl -X POST "http://localhost:8000/generate" \
  -H "Content-Type: application/json" \
  -d '{"query": "Design a microservices architecture", "provider": "groq", "model": "llama-3.3-70b-versatile"}'

# Test diagram endpoint (development)
curl "http://localhost:8000/test-diagram"
```

### Frontend Development
```bash
cd frontend
pnpm dev          # Development server
pnpm build        # Production build
pnpm lint         # Code linting
```

**Development Features:**
- **Test Button**: Use the "Test Architecture" button in the UI to render sample diagrams without API calls
- **Provider Selection**: Choose between Gemini, Groq, OpenRouter, and Ollama providers
- **Model Selection**: Specify custom model names for fine-tuned control
- **Interactive Canvas**: Drag, zoom, and pan the ReactFlow diagram for better exploration

---

## 📚 API Reference

### Core Endpoints

#### POST `/generate`
Generate architecture from requirements
```json
{
  "query": "Design a high-traffic e-commerce platform",
  "provider": "groq",  // optional: "gemini", "groq", "openrouter", "ollama"
  "model": "llama-3.3-70b-versatile",  // optional: specific model name
  "existing_diagram": {...},  // optional: JSON nodes/edges for refinement
  "existing_components": [...]  // optional: for refinement
}
```

#### GET `/test-diagram`
Returns a sample architecture diagram for development testing (no LLM tokens used)

#### GET `/health`
Service health check

### Response Format
```json
{
  "components": [
    {
      "name": "API Gateway",
      "type": "gateway"
    }
  ],
  "nodes": [
    {
      "id": "API_Gateway",
      "type": "architectureNode",
      "data": {"label": "API Gateway", "type": "Gateway"},
      "position": {"x": 100, "y": 100}
    }
  ],
  "edges": [
    {
      "id": "e0-API_Gateway-Core_API",
      "source": "API_Gateway",
      "target": "Core_API",
      "animated": false
    }
  ],
  "architecture": "High-level architecture description...",
  "scaling": "Horizontal scaling recommendations...",
  "constraints": {
    "budget_usd_month": 5000,
    "team_size": 5
  }
}
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Use TypeScript for frontend code
- Follow FastAPI best practices for backend
- Add tests for new features

---

## 📄 License

**MIT License** - See [LICENSE](LICENSE) for details

---

## 🙏 Acknowledgments

- **ChromaDB** for vector database capabilities
- **Sentence Transformers** for embedding generation
- **Mermaid.js** for diagram visualization
- **FastAPI** for robust API framework
- **Next.js** for modern React development

---
