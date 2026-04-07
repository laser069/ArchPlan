// 1. GLOBAL STATE - Keeps the design in memory and browser storage
let currentDiagramCode = localStorage.getItem("archplan_diagram") || "";

// Initialize UI on Page Load
window.onload = () => {
  const updateBtn = document.getElementById("update-btn");
  if (currentDiagramCode) {
    console.log("Restored previous session.");
    // Enable refine button if we have saved data
    setUpdateBtnState(true);
    // You could call an initial render here if desired: renderDiagram(currentDiagramCode);
  }
};

/**
 * Main Generation Function
 * @param {boolean} isUpdate - true for "Refine", false for "New Design"
 */
async function generate(isUpdate = false) {
  const queryInput = document.getElementById("query");
  const query = queryInput.value.trim();
  
  // UI Elements
  const genBtn = document.getElementById("gen-btn");
  const updateBtn = document.getElementById("update-btn");
  const statusText = document.getElementById("status-text");
  const spinner = document.getElementById("status-spinner");
  const diagArea = document.getElementById("diagram");
  const ragBadge = document.getElementById("rag-badge");

  // --- VALIDATION & SAFETY ---
  if (!query) return alert("Please enter a design request first.");
  
  if (isUpdate && !currentDiagramCode) {
    statusText.innerText = "⚠️ Generate a base design first!";
    statusText.classList.add("text-red-500");
    return;
  }

  // --- UI START STATE ---
  genBtn.disabled = true;
  updateBtn.disabled = true;
  spinner.classList.remove("hidden");
  statusText.classList.remove("text-red-500");
  
  if (isUpdate) {
    diagArea.classList.add("ring-2", "ring-emerald-500", "ring-opacity-50", "transition-all", "duration-500");
    statusText.innerText = "Refining existing architecture...";
  } else {
    statusText.innerText = "Analyzing requirements...";
  }

  try {
    // Artificial progress updates for UX (RTX 2050 wait time)
    setTimeout(() => { if(genBtn.disabled) statusText.innerText = "Consulting knowledge base..."; }, 3000);
    setTimeout(() => { if(genBtn.disabled) statusText.innerText = "Architect is drafting logic..."; }, 8000);

    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ 
        query: query,
        existing_diagram: isUpdate ? currentDiagramCode : null 
      })
    });

    if (!res.ok) throw new Error("Backend connection failed");

    const data = await res.json();

    // --- DATA PROCESSING ---
    if (data.diagram) {
        currentDiagramCode = data.diagram;
        localStorage.setItem("archplan_diagram", currentDiagramCode);
        setUpdateBtnState(true);
    }

    // Update Narrative Sections
    document.getElementById("architecture").innerText = data.architecture || "";
    document.getElementById("scaling").innerText = data.scaling || "";
    document.getElementById("architecture").classList.remove("italic", "text-slate-400");
    document.getElementById("scaling").classList.remove("italic", "text-slate-400");
    
    // Show RAG Badge
    ragBadge.classList.remove("hidden");

    // Render Components
    const compList = document.getElementById("components");
    compList.innerHTML = "";
    (data.components || []).forEach((c, i) => {
      const li = document.createElement("li");
      li.className = "flex justify-between items-center bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg opacity-0 translate-y-1 transition-all duration-300";
      li.innerHTML = `<span class="text-sm font-medium text-slate-700">${c.name}</span>
                      <span class="text-[9px] font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded uppercase">${c.type}</span>`;
      compList.appendChild(li);
      setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), i * 40);
    });

    // --- MERMAID RENDERING ---
    diagArea.innerHTML = "";
    const mermaidId = "id-" + Math.random().toString(36).substr(2, 9);
    
    if (currentDiagramCode.includes("graph")) {
      const { svg } = await mermaid.render(mermaidId, currentDiagramCode);
      diagArea.innerHTML = svg;
    } else {
      diagArea.innerHTML = "<p class='text-amber-600 text-xs'>Format error in diagram code.</p>";
    }

  } catch (err) {
    console.error(err);
    statusText.innerText = "❌ Generation failed.";
    statusText.classList.add("text-red-500");
  } finally {
    // --- UI CLEANUP ---
    genBtn.disabled = false;
    updateBtn.disabled = !currentDiagramCode; 
    spinner.classList.add("hidden");
    diagArea.classList.remove("ring-2", "ring-emerald-500", "ring-opacity-50");
    if (!statusText.classList.contains("text-red-500")) {
        statusText.innerText = "Design ready.";
    }
  }
}

/**
 * Utility to toggle the 'Refine' button styling
 */
function setUpdateBtnState(enabled) {
    const btn = document.getElementById("update-btn");
    if (enabled) {
        btn.disabled = false;
        btn.classList.remove("opacity-50", "cursor-not-allowed");
        btn.classList.add("hover:border-emerald-500", "hover:text-emerald-600");
    } else {
        btn.disabled = true;
        btn.classList.add("opacity-50", "cursor-not-allowed");
    }
}

/**
 * Clears the session and UI
 */
function resetState() {
  if (confirm("Wipe current design?")) {
    currentDiagramCode = "";
    localStorage.removeItem("archplan_diagram");
    location.reload();
  }
}