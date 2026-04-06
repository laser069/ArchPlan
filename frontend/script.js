async function generate() {
  const query = document.getElementById("query").value;

  const res = await fetch("http://localhost:8000/generate", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ query })
  });

  const data = await res.json();

  // 🔹 Components
  const compList = document.getElementById("components");
  compList.innerHTML = "";

  data.components.forEach(c => {
    const li = document.createElement("li");
    li.textContent = `${c.name} (${c.type})`;
    compList.appendChild(li);
  });

  // 🔹 Text
  document.getElementById("architecture").innerText = data.architecture;
  document.getElementById("scaling").innerText = data.scaling;

  // 🔥 Diagram (Mermaid)
  const diagramDiv = document.getElementById("diagram");
  diagramDiv.innerHTML = `<div class="mermaid">${data.diagram}</div>`;

  // re-render
  mermaid.init(undefined, diagramDiv);
}