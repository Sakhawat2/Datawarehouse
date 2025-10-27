// admin/static/auth.js

// ✅ Unified token management
function getToken() {
  return localStorage.getItem("token");
}

function getRole() {
  return localStorage.getItem("is_admin") === "true" ? "admin" : "user";
}

// ✅ Auth check on page load
function checkAuth(allowedFor = "both") {
  const token = getToken();
  const isAdmin = getRole() === "admin";

  if (!token) {
    console.warn("No token found — redirecting to login...");
    window.location.replace("/admin/login.html");
    return false;
  }

  if (allowedFor === "admin" && !isAdmin) {
    console.warn("User tried to access admin-only page — redirecting...");
    window.location.replace("/user/user.html");
    return false;
  }

  if (allowedFor === "user" && isAdmin) {
    console.warn("Admin tried to access user-only page — redirecting...");
    window.location.replace("/admin/index.html");
    return false;
  }

  return true;
}

// ✅ Logout function
function logout() {
  localStorage.clear();
  window.location.replace("/admin/login.html");
}

// ✅ Authenticated fetch wrapper
async function apiFetch(url, options = {}) {
  const token = getToken();
  if (!options.headers) options.headers = {};
  if (token) options.headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(url, options);

  if (res.status === 401) {
    console.warn("⚠️ Session expired — redirecting to login...");
    localStorage.clear();
    window.location.replace("/admin/login.html");
  }

  return res;
}
