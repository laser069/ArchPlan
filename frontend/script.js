// 1. GLOBAL STATE - Keeps the design in memory and browser storage
let currentDiagramCode = localStorage.getItem("archplan_diagram") || "";

// Initialize UI on Page Load
window.addEventListener('DOMContentLoaded', () => {
    console.log("ArchPlan Session Initialized");
    if (currentDiagramCode) {
        // Restore buttons and state if we have a saved design
        setUpdateBtnState(true);
        const diagArea = document.getElementById("diagram");
        diagArea.innerHTML = "<p class='text-slate-400 text-xs text-center italic'>Previous design loaded. Click 'Refine' to modify or 'Reset' to start fresh.</p>";
    }
});

/**
 * Main Generation Function
 * @param {boolean} isUpdate - true for "Refine", false for "New Design"
 * @param {Event} event - The click event passed from HTML
 */
async function generate(isUpdate = false, event = null) {
    // 2. CRITICAL: PREVENT PAGE REFRESH
    if (event) event.preventDefault();

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
        diagArea.classList.add("ring-2", "ring-emerald-500", "ring-opacity-50");
        statusText.innerText = "Refining existing architecture...";
    } else {
        statusText.innerText = "Analyzing requirements...";
    }

    try {
        // Artificial progress updates for UX (Helps with RTX 2050 wait time)
        const progressInterval = setInterval(() => {
            if (statusText.innerText.includes("Analyzing")) statusText.innerText = "Consulting knowledge base...";
            else if (statusText.innerText.includes("Consulting")) statusText.innerText = "Drafting system components...";
            else if (statusText.innerText.includes("Drafting")) statusText.innerText = "Finalizing Mermaid diagram...";
        }, 12000);

        // 3. BACKEND FETCH
        const res = await fetch("http://localhost:8000/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ 
                query: query,
                existing_diagram: isUpdate ? currentDiagramCode : null 
            })
        });

        clearInterval(progressInterval);

        if (!res.ok) throw new Error(`Backend Error: ${res.status}`);

        const data = await res.json();

        // --- DATA PROCESSING ---
        if (data.diagram) {
            currentDiagramCode = data.diagram;
            localStorage.setItem("archplan_diagram", currentDiagramCode);
        }

        // Update Text Content
        document.getElementById("architecture").innerText = data.architecture || "";
        document.getElementById("scaling").innerText = data.scaling || "";
        document.getElementById("architecture").classList.remove("italic", "text-slate-400");
        document.getElementById("scaling").classList.remove("italic", "text-slate-400");
        
        if (ragBadge) ragBadge.classList.remove("hidden");

        // 4. RENDER COMPONENTS LIST
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

        // 5. MERMAID RENDERING
        if (currentDiagramCode) {
            try {
                diagArea.innerHTML = ""; // Clear loader
                const mermaidId = "graph-" + Date.now(); // Unique ID for every render
                const { svg } = await mermaid.render(mermaidId, currentDiagramCode);
                diagArea.innerHTML = svg;
            } catch (mermaidError) {
                console.error("Mermaid Render Fail:", mermaidError);
                diagArea.innerHTML = `
                    <div class="p-4 bg-amber-50 rounded border border-amber-200">
                        <p class='text-amber-700 text-xs font-bold'>Diagram Logic Error</p>
                        <code class='block mt-2 text-[10px] text-slate-500 break-all'>${currentDiagramCode}</code>
                    </div>`;
            }
        }

    } catch (err) {
        console.error("Critical Failure:", err);
        statusText.innerText = "❌ Generation failed. Check backend console.";
        statusText.classList.add("text-red-500");
    } finally {
        // --- UI CLEANUP ---
        genBtn.disabled = false;
        spinner.classList.add("hidden");
        diagArea.classList.remove("ring-2", "ring-emerald-500", "ring-opacity-50");
        setUpdateBtnState(!!currentDiagramCode);
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
    if (!btn) return;
    if (enabled) {
        btn.disabled = false;
        btn.classList.remove("opacity-50", "cursor-not-allowed");
        btn.classList.add("hover:border-emerald-500", "hover:text-emerald-600");
    } else {
        btn.disabled = true;
        btn.classList.add("opacity-50", "cursor-not-allowed");
        btn.classList.remove("hover:border-emerald-500", "hover:text-emerald-600");
    }
}

/**
 * Clears the session and UI
 */
function resetState() {
    if (confirm("Wipe current design and start fresh?")) {
        currentDiagramCode = "";
        localStorage.removeItem("archplan_diagram");
        location.reload();
    }
}