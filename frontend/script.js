const LS = {
  diagram:      "ap_diagram",
  architecture: "ap_architecture",
  scaling:      "ap_scaling",
  constraints:  "ap_constraints",
  components:   "ap_components",
  provider:     "ap_provider", 
  model:        "ap_model" // Added to store custom model IDs
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
  const savedProvider = localStorage.getItem(LS.provider) || "groq";
  const savedModel = localStorage.getItem(LS.model) || "";
  
  $("provider-select").value = savedProvider;
  $("model-input").value = savedModel;
  
  if (state.architecture) $("architecture").textContent = state.architecture;
  if (state.scaling) $("scaling").textContent = state.scaling;
  
  if (state.architecture || state.scaling) {
    [$("architecture"), $("scaling")].forEach(el => el.classList.remove("italic", "text-slate-400"));
  }
  
  if (state.components.length > 0) updateComponentList(state.components);

  if (state.diagram) {
    setRefineEnabled(true);
    renderMermaid(state.diagram);
  }
});

async function generate(isRefine = false) {
  const query = $("query").value.trim();
  const provider = $("provider-select").value;
  const model = $("model-input").value.trim();

  if (!query) return alert("Please enter a prompt.");

  // Save selection preference
  localStorage.setItem(LS.provider, provider);
  localStorage.setItem(LS.model, model);

  setLoading(true, isRefine);

  if (isRefine) $("diagram-container").classList.add("refining");
  else $("diagram-container").classList.remove("refining");

  try {
    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        provider: provider,
        model: model || null, // Pass the dynamic model string
        existing_diagram:     isRefine ? state.diagram : null,
        existing_components:  isRefine ? state.components : null,
        cached_constraints:   isRefine ? state.constraints : null,
      }),
    });

    if (!res.ok) throw new Error(`Server Error: ${res.status}`);
    const data = await res.json();

    // Update State
    state.diagram = data.diagram;
    state.components = data.components;
    state.architecture = data.architecture;
    state.scaling = data.scaling;

    localStorage.setItem(LS.diagram, state.diagram);
    localStorage.setItem(LS.components, JSON.stringify(state.components));
    localStorage.setItem(LS.architecture, state.architecture);
    localStorage.setItem(LS.scaling, state.scaling);
    
    if (!isRefine && data.constraints) { 
        state.constraints = data.constraints; 
        localStorage.setItem(LS.constraints, JSON.stringify(state.constraints)); 
    }

    // Update UI
    $('architecture').textContent = state.architecture;
    $('scaling').textContent = state.scaling;
    [$("architecture"), $("scaling")].forEach(el => el.classList.remove("italic", "text-slate-400"));

    updateComponentList(data.components || []);
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

// ... (Rest of helper functions remain unchanged)
function updateComponentList(components) {
    const list = $("components");
    list.innerHTML = "";
    components.forEach((c, i) => {
      const li = document.createElement("li");
      li.className = "flex justify-between items-center bg-slate-50 border border-slate-100 px-2.5 py-1.5 rounded-lg text-xs opacity-0 translate-y-1 transition-all duration-300";
      li.innerHTML = `<span class="font-medium text-slate-700">${c.name}</span><span class="mono text-[9px] font-bold bg-indigo-50 text-indigo-700 px-1.5 py-0.5 rounded uppercase">${c.type}</span>`;
      list.appendChild(li);
      setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), i * 40);
    });
}

async function renderMermaid(code) {
  const el = $("diagram");
  try {
    const { svg } = await mermaid.render("id_" + Math.random().toString(36).substr(2, 9), code);
    el.innerHTML = svg;
    el.classList.add("bg-white");
    el.classList.remove("bg-slate-50");
  } catch (err) {
    console.error("Mermaid Render Error:", err);
    el.innerHTML = `<div class="p-4 bg-red-50 text-[10px] w-full"><p class="font-bold text-red-700">Syntax Error</p><code>${code}</code></div>`;
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
  if (!confirm("Wipe workspace?")) return;
  Object.values(LS).forEach(k => localStorage.removeItem(k));
  location.reload();
}

function copyDiagram() {
    if (!state.diagram) return;
    navigator.clipboard.writeText(state.diagram);
    alert("Copied!");
}