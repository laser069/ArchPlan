const LS = {
  diagram:      "ap_diagram",
  architecture: "ap_architecture",
  scaling:      "ap_scaling",
  constraints:  "ap_constraints",
  components:   "ap_components",
  provider:     "ap_provider", // "groq", "gemini", or "ollama"
};

let state = {
  diagram:      localStorage.getItem(LS.diagram) || "",
  architecture: localStorage.getItem(LS.architecture) || "",
  scaling:      localStorage.getItem(LS.scaling) || "",
  constraints:  JSON.parse(localStorage.getItem(LS.constraints) || "null"),
  components:   JSON.parse(localStorage.getItem(LS.components) || "[]"),
};

const $ = id => document.getElementById(id);

window.addEventListener("DOMContentLoaded", () => {
  // Initialize provider from storage, default to 'groq'
  const savedProvider = localStorage.getItem(LS.provider) || "groq";
  $("provider-select").value = savedProvider;
  
  // Restore UI State
  if (state.architecture) $("architecture").textContent = state.architecture;
  if (state.scaling) $("scaling").textContent = state.scaling;
  
  if (state.architecture || state.scaling) {
    [$("architecture"), $("scaling")].forEach(el => el.classList.remove("italic", "text-slate-400"));
  }
  
  if (state.components.length > 0) {
    updateComponentList(state.components);
  }

  if (state.diagram) {
    setRefineEnabled(true);
    renderMermaid(state.diagram);
  }
});

async function generate(isRefine = false) {
  const query = $("query").value.trim();
  if (!query) return alert("Please enter a prompt.");

  setLoading(true, isRefine);

  if (isRefine) $("diagram-container").classList.add("refining");
  else          $("diagram-container").classList.remove("refining");

  try {
    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        provider: $("provider-select").value,
        existing_diagram:     isRefine ? state.diagram : null,
        existing_components:  isRefine ? state.components : null,
        cached_constraints:   isRefine ? state.constraints : null,
      }),
    });

    if (!res.ok) throw new Error(`Server Error: ${res.status}`);
    const data = await res.json();

    // Update Global State & LocalStorage
    if (data.diagram)      { state.diagram = data.diagram; localStorage.setItem(LS.diagram, state.diagram); }
    if (data.components)   { state.components = data.components; localStorage.setItem(LS.components, JSON.stringify(state.components)); }
    if (data.architecture) { state.architecture = data.architecture; localStorage.setItem(LS.architecture, state.architecture); }
    if (data.scaling)      { state.scaling = data.scaling; localStorage.setItem(LS.scaling, state.scaling); }
    
    // Constraints are typically returned on new generations to be cached for future refinements
    if (!isRefine && data.constraints) { 
        state.constraints = data.constraints; 
        localStorage.setItem(LS.constraints, JSON.stringify(state.constraints)); 
    }

    // Update Text Content
    $('architecture').textContent = state.architecture;
    $('scaling').textContent = state.scaling;
    [$("architecture"), $("scaling")].forEach(el => el.classList.remove("italic", "text-slate-400"));

    // Animate Component List
    updateComponentList(data.components || []);

    // Render Diagram
    if (state.diagram) await renderMermaid(state.diagram);
    setStatus(isRefine ? "Refinement complete." : "Architecture ready.");

  } catch (err) {
    console.error(err);
    setStatus("Error: Connection failed.", true);
  } finally {
    setLoading(false, isRefine);
    setRefineEnabled(!!state.diagram);
  }
}

function updateComponentList(components) {
    const list = $("components");
    list.innerHTML = "";
    components.forEach((c, i) => {
      const li = document.createElement("li");
      li.className = "flex justify-between items-center bg-slate-50 border border-slate-100 px-2.5 py-1.5 rounded-lg text-xs opacity-0 translate-y-1 transition-all duration-300";
      li.innerHTML = `
        <span class="font-medium text-slate-700">${c.name}</span>
        <span class="mono text-[9px] font-bold bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded uppercase">${c.type}</span>
      `;
      list.appendChild(li);
      setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), i * 40);
    });
}

async function renderMermaid(code) {
  const el = $("diagram");
  try {
    // Generate a unique ID for each render to prevent Mermaid caching issues
    const { svg } = await mermaid.render("id_" + Math.random().toString(36).substr(2, 9), code);
    el.innerHTML = svg;
    el.classList.add("bg-white");
    el.classList.remove("bg-slate-50");
  } catch (err) {
    console.error("Mermaid Render Error:", err);
    el.innerHTML = `
      <div class="p-4 bg-red-50 border border-red-100 rounded text-[10px] w-full">
        <p class="font-bold text-red-700 mb-1">Diagram Syntax Error</p>
        <code class="text-slate-500 block bg-white p-2 rounded border border-red-50">${code}</code>
      </div>`;
  }
}

function setLoading(on, isRefine) {
  $("gen-btn").disabled = on;
  $("upd-btn").disabled = on;
  $("status-bar").classList.toggle("hidden", !on);
  if (on) $("status-text").textContent = isRefine ? "Refining design..." : "Architecting...";
}

function setStatus(msg, isError = false) {
  const el = $("status-text");
  el.textContent = msg;
  el.className = isError ? "text-red-500 font-bold" : "text-slate-400";
  $("status-bar").classList.remove("hidden");
  setTimeout(() => $("status-bar").classList.add("hidden"), 4000);
}

function setRefineEnabled(on) {
  const btn = $("upd-btn");
  btn.disabled = !on;
  btn.classList.toggle("opacity-40", !on);
  btn.classList.toggle("cursor-not-allowed", !on);
}

function resetState() {
  if (!confirm("Wipe workspace and start a new design?")) return;
  Object.values(LS).forEach(k => localStorage.removeItem(k));
  location.reload();
}

function copyDiagram() {
    if (!state.diagram) return;
    navigator.clipboard.writeText(state.diagram);
    alert("Mermaid code copied to clipboard!");
}