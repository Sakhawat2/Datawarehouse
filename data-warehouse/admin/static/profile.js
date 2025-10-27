const token = localStorage.getItem("token");

async function apiFetch(url, options = {}) {
  const headers = options.headers || {};
  headers["Authorization"] = `Bearer ${token}`;
  options.headers = headers;

  const res = await fetch(url, options);
  if (res.status === 401) {
    alert("Session expired. Please log in again.");
    window.location.href = "/admin/login.html";
  }
  return res;
}


// ─────────────────────────────────────────────
// Load profile info
// ─────────────────────────────────────────────
async function fetchProfile() {
  try {
    const res = await fetch("/api/profile", {
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` }
    });

    if (!res.ok) {
      window.location.href = "/admin/login.html";
      return;
    }

    const data = await res.json();
    document.getElementById("username").textContent = data.username;
    document.getElementById("roleBadge").textContent = data.is_admin ? "Admin" : "User";
    document.getElementById("roleBadge").classList.add(data.is_admin ? "bg-danger" : "bg-success");
    document.getElementById("createdAt").textContent = `Member since: ${new Date(data.created_at).toLocaleString()}`;
  } catch (err) {
    console.error("Error loading profile:", err);
  }
}

document.getElementById("passwordForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const oldPassword = document.getElementById("oldPassword").value;
  const newPassword = document.getElementById("newPassword").value;
  const msg = document.getElementById("message");

  const formData = new FormData();
  formData.append("old_password", oldPassword);
  formData.append("new_password", newPassword);

  try {
    const res = await fetch("/api/profile/update-password", {
      method: "PUT",
      headers: { Authorization: `Bearer ${localStorage.getItem("token")}` },
      body: formData,
    });

    const data = await res.json();
    msg.textContent = res.ok ? data.message : (data.detail || "❌ Failed to update password");
    msg.style.color = res.ok ? "green" : "red";
    if (res.ok) e.target.reset();
  } catch (err) {
    msg.textContent = "⚠️ Network error";
    msg.style.color = "red";
  }
});

fetchProfile();
