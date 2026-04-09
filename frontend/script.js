let currentDiagramCode = localStorage.getItem("archplan_diagram") || "";
let cachedConstraints = JSON.parse(localStorage.getItem("archplan_constraints") || "null");
let currentComponents = JSON.parse(localStorage.getItem("archplan_components") || "[]");

window.addEventListener('DOMContentLoaded', () => {
    // Set initial provider value from storage
    const savedProvider = localStorage.getItem("archplan_provider") || "gemini";
    document.getElementById("provider-select").value = savedProvider;

    if (currentDiagramCode) {
        setUpdateBtnState(true);
        const diagArea = document.getElementById("diagram");
        diagArea.innerHTML = "<p class='text-slate-400 text-xs text-center italic'>Previous design loaded. Click 'Refine' to modify or 'Reset' to start fresh.</p>";
        // Re-render if you want it visible on load:
        renderMermaid(currentDiagramCode);
    }
});

async function generate(isUpdate = false, event = null) {
    if (event) event.preventDefault();

    const queryInput = document.getElementById("query");
    const query = queryInput.value.trim();
    if (!query) return alert("Please enter a design request first.");

    // DOM Elements
    const genBtn = document.getElementById("gen-btn");
    const updateBtn = document.getElementById("update-btn");
    const statusText = document.getElementById("status-text");
    const spinner = document.getElementById("status-spinner");
    const diagArea = document.getElementById("diagram");
    const diagContainer = document.getElementById("diagram-container");
    const provider = document.getElementById("provider-select").value;

    // UI States
    genBtn.disabled = true;
    updateBtn.disabled = true;
    spinner.classList.remove("hidden");
    statusText.classList.remove("text-red-500");

    if (isUpdate) {
        diagContainer.classList.add("refining-active");
        statusText.innerText = "Applying changes...";
    } else {
        diagContainer.classList.remove("refining-active");
        statusText.innerText = "Analyzing requirements...";
    }

    try {
        const requestBody = {
            query: query,
            provider: provider,
            existing_diagram: isUpdate ? currentDiagramCode : null,
            existing_components: isUpdate ? currentComponents : null,
            cached_constraints: isUpdate ? cachedConstraints : null,
        };

        const res = await fetch("http://localhost:8000/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestBody)
        });

        if (!res.ok) throw new Error(`Backend Error: ${res.status}`);
        const data = await res.json();

        // 1. Update State & LocalStorage
        if (data.diagram) {
            currentDiagramCode = data.diagram;
            localStorage.setItem("archplan_diagram", currentDiagramCode);
        }
        if (data.components) {
            currentComponents = data.components;
            localStorage.setItem("archplan_components", JSON.stringify(currentComponents));
        }
        if (!isUpdate && data.constraints) {
            cachedConstraints = data.constraints;
            localStorage.setItem("archplan_constraints", JSON.stringify(cachedConstraints));
        }

        // 2. Update Text Content
        document.getElementById("architecture").innerText = data.architecture || "";
        document.getElementById("scaling").innerText = data.scaling || "";
        document.getElementById("architecture").classList.remove("italic", "text-slate-400");
        document.getElementById("scaling").classList.remove("italic", "text-slate-400");

        // 3. Render Components List
        const compList = document.getElementById("components");
        compList.innerHTML = "";
        (data.components || []).forEach((c, i) => {
            const li = document.createElement("li");
            li.className = "flex justify-between items-center bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg opacity-0 translate-y-1 transition-all duration-300";
            li.innerHTML = `
                <span class="text-sm font-medium text-slate-700">${c.name}</span>
                <span class="text-[9px] font-bold bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded uppercase">${c.type}</span>
            `;
            compList.appendChild(li);
            setTimeout(() => li.classList.remove("opacity-0", "translate-y-1"), i * 40);
        });

        // 4. Render Mermaid Diagram
        if (currentDiagramCode) {
            await renderMermaid(currentDiagramCode);
        }

    } catch (err) {
        console.error("Critical Failure:", err);
        statusText.innerText = "❌ Generation failed. Check backend console.";
        statusText.classList.add("text-red-500");
    } finally {
        genBtn.disabled = false;
        spinner.classList.add("hidden");
        setUpdateBtnState(!!currentDiagramCode);
        if (!statusText.classList.contains("text-red-500")) {
            statusText.innerText = isUpdate ? "Design refined." : "Design ready.";
        }
    }
}

async function renderMermaid(code) {
    const diagArea = document.getElementById("diagram");
    try {
        diagArea.innerHTML = "";
        const mermaidId = "graph-" + Date.now();
        const { svg } = await mermaid.render(mermaidId, code);
        diagArea.innerHTML = svg;
    } catch (err) {
        diagArea.innerHTML = `<div class="p-4 bg-amber-50 rounded border border-amber-200">
            <p class='text-amber-700 text-xs font-bold'>Render Error</p>
            <code class='block mt-2 text-[10px] text-slate-500 break-all'>${code}</code>
        </div>`;
    }
}

function setUpdateBtnState(enabled) {
    const btn = document.getElementById("update-btn");
    if (!btn) return;
    if (enabled) {
        btn.disabled = false;
        btn.classList.remove("opacity-50", "cursor-not-allowed");
        btn.classList.add("hover:border-emerald-500", "hover:text-emerald-600");
    } else {
        btn.disabled = true;
        btn.classList.add("opacity-50", "cursor-not-allowed");
    }
}

function resetState() {
    if (confirm("Wipe current design and start fresh?")) {
        currentDiagramCode = "";
        cachedConstraints = null;
        currentComponents = [];
        localStorage.clear();
        location.reload();
    }
}