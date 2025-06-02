const token = localStorage.getItem("access_token");

if (!token) {
  alert("You're not logged in.");
  window.location.href = "/client/login";
}

function secureFetch(url, options = {}) {
  return fetch(url, {
    ...options,
    headers: {
      ...(options.headers || {}),
      Authorization: "Bearer " + token
    }
  });
}
