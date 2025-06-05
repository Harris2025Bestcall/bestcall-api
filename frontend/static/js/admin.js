// admin.js – Simplified for single-dealer system ops portal

document.addEventListener("DOMContentLoaded", () => {
  const upload = (url, formData, successMsg) => {
    fetch(url, {
      method: "POST",
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        console.log(data);
        alert(successMsg || "Upload complete");
      })
      .catch(err => alert("Upload failed: " + err));
  };

  // --- Upload buttons ---
  document.getElementById("upload-inventory")?.addEventListener("click", () => {
    const file = document.getElementById("inventory-file").files[0];
    if (!file) return alert("Select an inventory file.");
    const fd = new FormData();
    fd.append("file", file);
    upload("/upload-inventory", fd, "Inventory uploaded");
  });

  document.getElementById("upload-bank-summary")?.addEventListener("click", () => {
    const file = document.getElementById("bank-summary-file").files[0];
    if (!file) return alert("Select a bank decision file.");
    const fd = new FormData();
    fd.append("file", file);
    upload("/upload-bank-summary", fd, "Bank summary uploaded");
  });

  document.getElementById("upload-credit-files")?.addEventListener("click", () => {
    const appFile = document.getElementById("credit-app").files[0];
    const reportFile = document.getElementById("credit-report").files[0];
    if (!appFile || !reportFile) return alert("Upload both credit app and report.");
    const fd = new FormData();
    fd.append("credit_app", appFile);
    fd.append("credit_report", reportFile);
    upload("/upload-training-example", fd, "Training example uploaded");
  });

  document.getElementById("upload-bank-results")?.addEventListener("click", () => {
    const files = document.getElementById("actual-bank-files").files;
    const clientId = document.getElementById("actual-client-id").value;
    if (!files.length || !clientId) return alert("Enter client ID and select PDF files.");
    const fd = new FormData();
    fd.append("client_id", clientId);
    for (let file of files) fd.append("files", file);
    upload("/upload-actual-results", fd, "Actual results uploaded");
  });

  // --- Generate Summary ---
  document.getElementById("generate-summary")?.addEventListener("click", () => {
    fetch("/generate-summary", { method: "POST" })
      .then(res => res.json())
      .then(data => {
        alert("Summary generated");
        loadPreview();
        loadMetrics();
        loadProgress();
      })
      .catch(err => alert("Failed to generate summary."));
  });

  // --- Load preview ---
  function loadPreview() {
    fetch("/summary-preview")
      .then(res => res.text())
      .then(markdown => {
        document.getElementById("summary-preview").innerText = markdown;
      })
      .catch(() => {
        document.getElementById("summary-preview").innerText = "No summary available yet.";
      });
  }

  // --- Load metrics ---
  function loadMetrics() {
    fetch("/metrics")
      .then(res => res.json())
      .then(data => {
        document.getElementById("client-count").innerText = data.clients || 0;
        document.getElementById("avg-fico").innerText = data.avg_fico || "N/A";
        document.getElementById("approval-rate").innerText = data.approval_rate || "0%";
      });
  }

  // --- Load progress ---
  function loadProgress() {
    fetch("/progress")
      .then(res => res.json())
      .then(data => {
        document.getElementById("progress-bar").style.width = data.completion + "%";
        document.getElementById("progress-text").innerText = data.message;
      });
  }

  // Auto-load metrics and summary on page load
  loadPreview();
  loadMetrics();
  loadProgress();
});
