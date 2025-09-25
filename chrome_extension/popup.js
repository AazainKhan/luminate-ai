document.getElementById("ask").addEventListener("click", async () => {
  const q = document.getElementById("q").value;
  document.getElementById("out").innerText = "Searching...";
  try {
    const resp = await fetch("http://localhost:8000/ask", {
      method: "POST",
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify({question: q})
    });
    const j = await resp.json();
    document.getElementById("out").innerText = JSON.stringify(j, null, 2);
  } catch (e) {
    document.getElementById("out").innerText = "Error: " + e.toString();
  }
});