async function generate() {
  const queryInput = document.getElementById("query");
  const query = queryInput.value.trim();

  if (!query) return alert("Please enter a design request.");

  // UI Elements
  const btn = document.getElementById("gen-btn");
  const spinner = document.getElementById("status-spinner");
  const statusText = document.getElementById("status-text");
  const ragBadge = document.getElementById("rag-badge");
  const compList = document.getElementById("components");
  const diagDiv = document.getElementById("diagram");

  // Reset UI for new generation
  btn.disabled = true;
  btn.innerText = "Processing...";
  spinner.classList.remove("hidden");
  ragBadge.classList.add("hidden");
  
  // Start with step 1
  statusText.innerText = "Analyzing requirements & constraints...";

  try {
    // Optional: Simulate stage updates if your backend doesn't support streaming
    // This makes the 30s wait feel faster to the user
    setTimeout(() => { if(btn.disabled) statusText.innerText = "Searching internal knowledge base..."; }, 3000);
    setTimeout(() => { if(btn.disabled) statusText.innerText = "Architect is designing the system..."; }, 7000);

    const res = await fetch("http://localhost:8000/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });

    if (!res.ok) throw new Error("Backend failed to respond");

    const data = await res.json();

    // 1. Show RAG Badge
    ragBadge.classList.remove("hidden");

    // 2. Render Components with a slightly nicer fade-in effect
    compList.innerHTML = "";
    data.components.forEach((c, index) => {
      const li = document.createElement("li");
      li.className = "flex justify-between items-center bg-slate-50 border border-slate-100 px-3 py-2 rounded-lg hover:bg-white transition-all duration-300 translate-y-2 opacity-0";
      li.innerHTML = `
        <span class="font-medium text-slate-700">${c.name}</span>
        <span class="text-[10px] font-bold bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full uppercase">${c.type}</span>
      `;
      compList.appendChild(li);
      // Staggered animation
      setTimeout(() => {
        li.classList.remove('translate-y-2', 'opacity-0');
      }, index * 50);
    });

    // 3. Update Narrative Text
    document.getElementById("architecture").innerText = data.architecture;
    document.getElementById("scaling").innerText = data.scaling;
    document.getElementById("architecture").classList.remove("italic", "text-gray-400");
    document.getElementById("scaling").classList.remove("italic", "text-gray-400");

    // 4. Render Diagram (Mermaid) with Error Handling
    diagDiv.innerHTML = ""; 
    const mermaidId = "graph-" + Math.floor(Math.random() * 10000);
    
    try {
      // Ensure the diagram string isn't empty or invalid
      if (data.diagram && data.diagram.includes("graph")) {
        const { svg } = await mermaid.render(mermaidId, data.diagram);
        diagDiv.innerHTML = svg;
      } else {
        diagDiv.innerHTML = "<p class='text-amber-500 text-sm'>Generated diagram format was invalid.</p>";
      }
    } catch (mermaidErr) {
      console.error("Mermaid Render Error:", mermaidErr);
      diagDiv.innerHTML = "<p class='text-red-500 text-sm'>Failed to render visual diagram. Raw code: <br><code class='text-xs'>" + data.diagram + "</code></p>";
    }

  } catch (err) {
    console.error("Generation Error:", err);
    alert("Generation failed. Please check if the backend server and Ollama are running.");
  } finally {
    btn.disabled = false;
    btn.innerText = "Generate Architecture";
    spinner.classList.add("hidden");
  }
}