const LS = {
  diagram:      "ap_diagram",
  architecture: "ap_architecture",
  scaling:      "ap_scaling",
  constraints:  "ap_constraints",
  components:   "ap_components",
  provider:     "ap_provider",
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
  $("provider-select").value = localStorage.getItem(LS.provider) || "gemini";
  
  if (state.architecture) $("architecture").textContent = state.architecture;
  if (state.scaling) $("scaling").textContent = state.scaling;
  if (state.architecture || state.scaling) {
    [$("architecture"), $("scaling")].forEach(el => el.classList.remove("italic", "text-slate-400"));
  }
  
  if (state.diagram) {
    setRefineEnabled(true);
    renderMermaid(state.diagram);
  }
});

async function generate(isRefine = false) {
  const query = $("query").value.trim();
  if (!query) return alert("Enter a design request first.");

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

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (data.diagram)    { state.diagram = data.diagram; localStorage.setItem(LS.diagram, state.diagram); }
    if (data.components) { state.components = data.components; localStorage.setItem(LS.components, JSON.stringify(state.components)); }
    if (data.architecture) { state.architecture = data.architecture; localStorage.setItem(LS.architecture, state.architecture); }
    if (data.scaling) { state.scaling = data.scaling; localStorage.setItem(LS.scaling, state.scaling); }
    if (!isRefine && data.constraints) { state.constraints = data.constraints; localStorage.setItem(LS.constraints, JSON.stringify(state.constraints)); }

    $('architecture').textContent = state.architecture;
    $('scaling').textContent = state.scaling;
    [$("architecture"), $("scaling")].forEach(el => el.classList.remove("italic", "text-slate-400"));

    $("components").innerHTML = "";
    (data.components || []).forEach((c, i) => {
      const li = document.createElement("li");
      li.className = "flex justify-between items-center bg-slate-50 border border-slate-100 px-2.5 py-1.5 rounded-lg text-xs opacity-0 translate-y-1 transition-all duration-300";
      li.innerHTML = `<span class="font-medium text-slate-700">${c.name}</span><span class="mono text-[9px] font-bold bg-violet-50 text-violet-700 px-1.5 py-0.5 rounded uppercase">${c.type}</span>`;
      $("components").appendChild(li);
      setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), i * 35);
    });

    if (state.diagram) await renderMermaid(state.diagram);
    setStatus(isRefine ? "Refined." : "Ready.");

  } catch (err) {
    console.error(err);
    setStatus("Failed — check backend.", true);
  } finally {
    setLoading(false, isRefine);
    setRefineEnabled(!!state.diagram);
  }
}

async function renderMermaid(code) {
  const el = $("diagram");
  el.innerHTML = "";
  try {
    const { svg } = await mermaid.render("g" + Date.now(), code);
    el.innerHTML = svg;
  } catch {
    el.innerHTML = `<div class="p-3 bg-amber-50 border border-amber-200 rounded text-[10px]">
      <p class="font-bold text-amber-700 mb-1">Render error</p>
      <code class="text-slate-500 break-all">${code}</code>
    </div>`;
  }
}

function setLoading(on, isRefine) {
  $("gen-btn").disabled = on;
  $("upd-btn").disabled = on;
  $("status-bar").classList.toggle("hidden", !on);
  if (on) $("status-text").textContent = isRefine ? "Applying changes..." : "Analyzing...";
}

function setStatus(msg, isError = false) {
  const el = $("status-text");
  el.textContent = msg;
  el.className = isError ? "text-red-500" : "text-slate-400";
  $("status-bar").classList.remove("hidden");
  setTimeout(() => $("status-bar").classList.add("hidden"), 3000);
}

function setRefineEnabled(on) {
  const btn = $("upd-btn");
  btn.disabled = !on;
  btn.classList.toggle("opacity-40", !on);
  btn.classList.toggle("cursor-not-allowed", !on);
}

function resetState() {
  if (!confirm("Wipe current design and start fresh?")) return;
  Object.values(LS).forEach(k => localStorage.removeItem(k));
  location.reload();
}