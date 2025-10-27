document.getElementById("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const username = document.getElementById("username").value.trim();
  const password = document.getElementById("password").value.trim();

  if (!username || !password) {
    alert("⚠️ Please enter both username and password");
    return;
  }

  const formData = new FormData();
  formData.append("username", username);
  formData.append("password", password);

  try {
    const res = await fetch("/api/login", {
      method: "POST",
      body: formData,
    });

    const data = await res.json();

    if (!res.ok) {
      alert(data.detail || "❌ Invalid username or password");
      return;
    }

    // ✅ Save login info
    localStorage.clear();
    localStorage.setItem("token", data.access_token);
    localStorage.setItem("username", username);
    localStorage.setItem("is_admin", data.is_admin ? "true" : "false");

    console.log("✅ Login successful:", data);

    // ✅ Short delay ensures Chrome processes localStorage before redirect
    setTimeout(() => {
      if (data.is_admin === true || data.is_admin === "true") {
        console.log("→ Redirecting admin to /admin/index.html");
        window.location.replace("/admin/index.html");
      } else {
        console.log("→ Redirecting user to /user/user.html");
        window.location.replace("/user/user.html");
      }
    }, 400);
  } catch (err) {
    console.error("Login failed:", err);
    alert("❌ Server error, please try again later");
  }
});

// 🟢 Auto redirect if already logged in
document.addEventListener("DOMContentLoaded", () => {
  const token = localStorage.getItem("token");
  const isAdmin = localStorage.getItem("is_admin");

  if (token) {
    setTimeout(() => {
      if (isAdmin === "true") {
        window.location.replace("/admin/index.html");
      } else {
        window.location.replace("/user/user.html");
      }
    }, 300);
  }
});
