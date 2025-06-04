// 🔐 Get token from local storage
const token = localStorage.getItem("access_token");

// 🔐 Redirect to login if token is missing
if (!token) {
  alert("Admin access requires login.");
  window.location.href = "/client/login";
}

// 🔐 Secure fetch wrapper that auto-injects the token
function secureFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: "Bearer " + token,
    },
  });
}

// 🔁 Upload function for baseline data
async function uploadFile(inputId, route, uploadedBtnId, uploadBtnId, updateBtnId, statusId) {
  const dealerId = document.getElementById("dealer_id").value;
  const fileInput = document.getElementById(inputId);
  const file = fileInput.files[0];
  const statusEl = document.getElementById(statusId);

  if (!file) return alert("Please choose a file first.");

  const formData = new FormData();
  formData.append("dealer_id", dealerId);
  formData.append(inputId === "bank_summary_file" ? "bank_summary" : "inventory", file);

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
    statusEl.classList.remove("hidden");
  } else {
    statusEl.textContent = "❌ Upload failed: " + (data?.detail || "Unknown error");
    statusEl.className = "text-red-400 text-sm mt-2";
    statusEl.classList.remove("hidden");
  }
}

// 🧠 Summary + metrics + bindings
window.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await secureFetch("/metrics");
    if (!res.ok) throw new Error("Token rejected.");
  } catch (err) {
    alert("Access denied. Please log in again.");
    localStorage.removeItem("access_token");
    window.location.href = "/client/login";
    return;
  }

  const generateButton = document.getElementById("generate_summary");
  const dealerSelect = document.getElementById("dealer_id");
  const summaryPreview = document.getElementById("summaryPreview");
  const summaryTimestamp = document.getElementById("summaryTimestamp");

  // ⬆️ Upload Bank Summary
  document.getElementById("bank_summary_upload").onclick = () =>
    uploadFile(
      "bank_summary_file",
      "upload-bank-summary",
      "bank_summary_uploaded",
      "bank_summary_upload",
      "bank_summary_update",
      "bank_summary_status"
    );

  // ⬆️ Upload Inventory
  document.getElementById("inventory_upload").onclick = () =>
    uploadFile(
      "inventory_file",
      "upload-inventory",
      "inventory_uploaded",
      "inventory_upload",
      "inventory_update",
      "inventory_status"
    );

  // 🔁 Reset Bank Summary upload
  document.getElementById("bank_summary_update").onclick = () => {
    document.getElementById("bank_summary_upload").classList.remove("hidden");
    document.getElementById("bank_summary_uploaded").classList.add("hidden");
    document.getElementById("bank_summary_update").classList.add("hidden");
  };

  // 🔁 Reset Inventory upload
  document.getElementById("inventory_update").onclick = () => {
    document.getElementById("inventory_upload").classList.remove("hidden");
    document.getElementById("inventory_uploaded").classList.add("hidden");
    document.getElementById("inventory_update").classList.add("hidden");
  };

  // 🧠 Summary Generation Button Logic
  if (generateButton && dealerSelect && summaryPreview) {
    generateButton.addEventListener("click", async () => {
      const dealerId = dealerSelect.value;

      generateButton.disabled = true;
      generateButton.textContent = "Generating...";
      summaryPreview.textContent = "⏳ Generating summary...";

      try {
        const res = await secureFetch(`/system-operations/train/${dealerId}/summary`);
        const result = await res.json();

        if (!res.ok) {
          summaryPreview.textContent = `⚠️ Error: ${result.detail || "Generation failed."}`;
        } else {
          const previewRes = await secureFetch(`/system-operations/train/${dealerId}/summary/preview`);
          const markdown = await previewRes.text();
          summaryPreview.textContent = markdown;

          const now = new Date().toLocaleString();
          summaryTimestamp.textContent = now;
        }
      } catch (err) {
        console.error(err);
        summaryPreview.textContent = "❌ Server error during summary generation.";
      }

      generateButton.disabled = false;
      generateButton.textContent = "Generate bank_patterns_summary.md";
    });
  }
});
