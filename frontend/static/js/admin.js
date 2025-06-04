// Get token from local storage
const token = localStorage.getItem("access_token");

// Redirect to login if token is missing
if (!token) {
  alert("Admin access requires login.");
  window.location.href = "/client/login";
}

// Secure fetch wrapper that auto-injects the token
function secureFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: "Bearer " + token
    }
  });
}

// Auth check + summary generation setup
window.addEventListener("DOMContentLoaded", async () => {
  try {
    // Verify token with a protected endpoint
    const res = await secureFetch("/metrics");

    if (!res.ok) {
      throw new Error("Token rejected.");
    }
  } catch (err) {
    alert("Access denied. Please log in again.");
    localStorage.removeItem("access_token");
    window.location.href = "/client/login";
    return;
  }

  // Generate Summary Button
  const generateButton = document.getElementById("generate-summary-button");
  if (generateButton) {
    generateButton.addEventListener("click", async () => {
      const dealerId = document.querySelector("#dealer-select").value;

      try {
        const res = await secureFetch(`/system-operations/train/${dealerId}/summary`, {
          method: "POST"
        });

        const result = await res.json();

        if (res.ok) {
          alert("Summary generated successfully.");
          console.log("Summary path:", result.summary_path);
        } else {
          alert("Error: " + result.detail);
        }
      } catch (err) {
        alert("Error creating summary.");
        console.error(err);
      }
    });
  }
});
