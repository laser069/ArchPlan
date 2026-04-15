const LS = {
    diagram: "ap_diagram",
    architecture: "ap_architecture",
    scaling: "ap_scaling",
    constraints: "ap_constraints",
    components: "ap_components",
    provider: "ap_provider", 
    model: "ap_model"
};

let state = {
    diagram: localStorage.getItem(LS.diagram) || "",
    architecture: localStorage.getItem(LS.architecture) || "",
    scaling: localStorage.getItem(LS.scaling) || "",
    constraints: JSON.parse(localStorage.getItem(LS.constraints) || "null"),
    components: JSON.parse(localStorage.getItem(LS.components) || "[]"),
};

const $ = id => document.getElementById(id);

window.addEventListener("DOMContentLoaded", () => {
    $("provider-select").value = localStorage.getItem(LS.provider) || "groq";
    $("model-input").value = localStorage.getItem(LS.model) || "";
    
    if (state.architecture) $("architecture").innerHTML = state.architecture;
    if (state.scaling) $("scaling").innerHTML = state.scaling;
    if (state.components.length > 0) updateComponentList(state.components);
    if (state.diagram) {
        setRefineEnabled(true);
        renderMermaid(state.diagram);
    }
});

async function generate(isRefine = false) {
    const query = $("query").value.trim();
    if (!query) return;

    localStorage.setItem(LS.provider, $("provider-select").value);
    localStorage.setItem(LS.model, $("model-input").value);

    setLoading(true, isRefine);

    try {
        const res = await fetch("http://localhost:8000/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                query,
                provider: $("provider-select").value,
                model: $("model-input").value || null,
                existing_diagram: isRefine ? state.diagram : null,
                existing_components: isRefine ? state.components : null,
            }),
        });

        const data = await res.json();
        
        state = { ...state, ...data };
        Object.keys(data).forEach(key => {
            const storageKey = LS[key];
            if (storageKey) localStorage.setItem(storageKey, typeof data[key] === 'object' ? JSON.stringify(data[key]) : data[key]);
        });

        $("architecture").innerHTML = state.architecture;
        $("scaling").innerHTML = state.scaling;
        updateComponentList(state.components);
        if (state.diagram) await renderMermaid(state.diagram);
        
        setStatus(isRefine ? "Sync_Complete" : "Design_Generated");
    } catch (err) {
        setStatus("System_Error", true);
    } finally {
        setLoading(false, isRefine);
        setRefineEnabled(!!state.diagram);
    }
}

function updateComponentList(components) {
    const list = $("components");
    list.innerHTML = "";
    components.forEach((c) => {
        const li = document.createElement("li");
        li.className = "flex justify-between items-baseline py-1.5 border-b border-black/[0.03]";
        li.innerHTML = `
            <span class="text-[11px] font-bold uppercase tracking-tighter text-black/80">${c.name}</span>
            <span class="mono text-[9px] opacity-40 lowercase italic">${c.type}</span>
        `;
        list.appendChild(li);
    });
}

async function renderMermaid(code) {
    const el = $("diagram");
    try {
        const { svg } = await mermaid.render("id_" + Math.random().toString(36).substr(2, 9), code);
        el.innerHTML = svg;
    } catch (err) {
        el.innerHTML = `<div class="mono text-[10px] text-red-600 bg-red-50 p-4">Syntax_Error: check_console</div>`;
    }
}

function setLoading(on, isRefine) {
    $("gen-btn").disabled = on;
    $("upd-btn").disabled = on;
    $("status-bar").classList.toggle("hidden", !on);
}

function setStatus(msg, isError = false) {
    const el = $("status-text");
    el.textContent = msg.toUpperCase();
    el.className = isError ? "text-red-600 mono text-[9px]" : "mono text-[9px]";
    $("status-bar").classList.remove("hidden");
    setTimeout(() => $("status-bar").classList.add("hidden"), 3000);
}

function setRefineEnabled(on) {
    $("upd-btn").disabled = !on;
}

function resetState() {
    if (confirm("CONFIRM_SYSTEM_WIPE?")) {
        localStorage.clear();
        location.reload();
    }
}

function copyDiagram() {
    if (!state.diagram) return;
    navigator.clipboard.writeText(state.diagram);
}