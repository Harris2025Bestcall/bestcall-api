// 🔐 Get token from local storage
const token = localStorage.getItem("access_token");

// 🔐 Redirect to login if token is missing
if (!token) {
  alert("Admin access requires login.");
  window.location.href = "/client/login";
}

// 🔐 Secure fetch wrapper with auth header
function secureFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: "Bearer " + token,
    },
  });
}

// 📤 Upload file (Bank Summary or Inventory)
async function uploadFile(inputId, route, uploadedBtnId, uploadBtnId, updateBtnId, statusId) {
  const dealerId = document.getElementById("dealer_id").value;
  const fileInput = document.getElementById(inputId);
  const file = fileInput?.files?.[0];
  const statusEl = document.getElementById(statusId);

  if (!file) return alert("Please choose a file first.");

  const formData = new FormData();
  formData.append("dealer_id", dealerId);
  formData.append(inputId === "bank_summary_file" ? "bank_summary" : "inventory", file);

  try {
    const res = await secureFetch(`/admin/${route}`, {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (res.ok) {
      document.getElementById(uploadBtnId).classList.add("hidden");
      document.getElementById(uploadedBtnId).classList.remove("hidden");
      document.getElementById(updateBtnId).classList.remove("hidden");

      statusEl.textContent = "✅ Upload successful";
      statusEl.className = "text-green-400 text-sm mt-2";
    } else {
      throw new Error(data?.detail || "Unknown error");
    }
  } catch (err) {
    statusEl.textContent = `❌ Upload failed: ${err.message}`;
    statusEl.className = "text-red-400 text-sm mt-2";
  }
}

// 📊 Fetch metrics and progress
async function fetchDealerMetrics(dealerId) {
  try {
    const res = await secureFetch(`/admin/system-operations/train/${dealerId}/metrics`);
    const data = await res.json();

    document.getElementById("metricClients").textContent = data.total_clients;
    document.getElementById("metricFICO").textContent = data.average_fico;
    document.getElementById("metricApproval").textContent = `${data.approval_rate}%`;
  } catch (err) {
    console.error("Error loading metrics:", err);
  }
}

async function fetchTrainingProgress(dealerId) {
  try {
    const res = await secureFetch(`/admin/system-operations/train/${dealerId}/progress`);
    const data = await res.json();

    const bar = document.getElementById("progressBar");
    const label = document.getElementById("progressLabel");

    bar.style.width = `${data.progress}%`;
    label.textContent = `AI trained on ${data.progress}% (${data.trained} of ${data.target} required clients)`;
  } catch (err) {
    document.getElementById("progressLabel").textContent = "❌ Could not load training progress.";
  }
}

// 🧠 Generate Summary Handler
async function handleSummaryGeneration() {
  const dealerId = document.getElementById("dealer_id").value;
  const generateButton = document.getElementById("generate_summary");
  const preview = document.getElementById("summaryPreview");
  const timestamp = document.getElementById("summaryTimestamp");

  generateButton.disabled = true;
  generateButton.textContent = "Generating...";
  preview.textContent = "⏳ Generating summary...";

  try {
    const res = await secureFetch(`/admin/system-operations/train/${dealerId}/summary`);
    const result = await res.json();

    if (!res.ok) {
      preview.textContent = `⚠️ Error: ${result.detail || "Summary failed."}`;
    } else {
      const previewRes = await secureFetch(`/admin/system-operations/train/${dealerId}/summary/preview`);
      const text = await mdRes.text();
      preview.textContent = text;
      timestamp.textContent = new Date().toLocaleString();
    }
  } catch (err) {
    preview.textContent = "❌ Server error during summary generation.";
  }

  generateButton.disabled = false;
  generateButton.textContent = "Generate bank_patterns_summary.md";
}

// 🚀 Main entry point
window.addEventListener("DOMContentLoaded", async () => {
  const dealerId = document.getElementById("dealer_id").value;

  try {
    const res = await secureFetch("/metrics");
    if (!res.ok) throw new Error("Session expired.");
  } catch {
    alert("Session expired. Please log in again.");
    localStorage.removeItem("access_token");
    window.location.href = "/client/login";
    return;
  }

  // 🔗 Upload bindings
  document.getElementById("bank_summary_upload").onclick = () =>
    uploadFile("bank_summary_file", "upload-bank-summary", "bank_summary_uploaded", "bank_summary_upload", "bank_summary_update", "bank_summary_status");

  document.getElementById("inventory_upload").onclick = () =>
    uploadFile("inventory_file", "upload-inventory", "inventory_uploaded", "inventory_upload", "inventory_update", "inventory_status");

  // 🔄 Reset buttons
  document.getElementById("bank_summary_update").onclick = () => {
    document.getElementById("bank_summary_upload").classList.remove("hidden");
    document.getElementById("bank_summary_uploaded").classList.add("hidden");
    document.getElementById("bank_summary_update").classList.add("hidden");
  };

  document.getElementById("inventory_update").onclick = () => {
    document.getElementById("inventory_upload").classList.remove("hidden");
    document.getElementById("inventory_uploaded").classList.add("hidden");
    document.getElementById("inventory_update").classList.add("hidden");
  };

  // 🧠 Summary
  document.getElementById("generate_summary").onclick = handleSummaryGeneration;

  // Load initial training metrics
  fetchDealerMetrics(dealerId);
  fetchTrainingProgress(dealerId);
});
