async function generate() {
  const query = document.getElementById("query").value;

  if (!query) return alert("Enter a query");

  const button = document.querySelector("button");
  button.disabled = true;
  button.innerText = "Generating...";

  try {
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

  li.className = "flex justify-between bg-gray-50 px-3 py-2 rounded";

  li.innerHTML = `
    <span>${c.name}</span>
    <span class="text-xs text-gray-500">${c.type}</span>
  `;

  compList.appendChild(li);
});

    // 🔹 Text
    document.getElementById("architecture").innerText = data.architecture;
    document.getElementById("scaling").innerText = data.scaling;

    // 🔥 Diagram (FIXED WAY)
    const diagramDiv = document.getElementById("diagram");
    diagramDiv.innerHTML = "";

    const id = "mermaid-" + Date.now();

    try {
      const { svg } = await mermaid.render(id, data.diagram);
      diagramDiv.innerHTML = svg;
    } catch (err) {
      console.error(err);
      diagramDiv.innerText = "Diagram failed to render";
    }

  } catch (err) {
    console.error(err);
    alert("Something went wrong");
  }

  button.disabled = false;
  button.innerText = "Generate";
}