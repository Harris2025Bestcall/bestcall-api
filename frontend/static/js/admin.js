const token = localStorage.getItem("access_token");

// Redirect to login if token is missing
if (!token) {
  alert("Admin access requires login.");
  window.location.href = "/client/login";
}

// Inject token for future API requests
function secureFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: "Bearer " + token
    }
  });
}

// Optional: Check auth when page loads
window.addEventListener("DOMContentLoaded", async () => {
  try {
    const res = await fetch("/metrics", {
      headers: {
        Authorization: "Bearer " + token
      }
    });

    if (!res.ok) {
      throw new Error("Token rejected.");
    }
  } catch (err) {
    alert("Access denied. Please log in again.");
    localStorage.removeItem("access_token");
    window.location.href = "/client/login";
  }
});
