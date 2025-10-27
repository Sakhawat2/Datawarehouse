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


// data-warehouse/admin/static/files.js
async function loadFiles() {
  const tbody = document.getElementById("filesTableBody");
  tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Loading...</td></tr>`;

  try {
    const res = await fetch("/api/files");
    const files = await res.json();

    if (!Array.isArray(files) || files.length === 0) {
      tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No files uploaded yet.</td></tr>`;
      return;
    }

    tbody.innerHTML = "";
    files.forEach(f => {
      const ext = f.filename.split(".").pop().toLowerCase();
      const isImage = ["jpg", "jpeg", "png", "gif"].includes(ext);

      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${f.filename}</td>
        <td>${isImage ? `<img src="/api/files/download/${f.filename}" height="50">` : "—"}</td>
        <td>${f.size}</td>
        <td>
          <a href="/api/files/download/${f.filename}" class="btn btn-sm btn-primary me-2" download>⬇️ Download</a>
          <button class="btn btn-sm btn-danger" onclick="deleteFile('${f.filename}')">🗑️ Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading files:", err);
    tbody.innerHTML = `<tr><td colspan="4" class="text-center text-danger">Error loading files</td></tr>`;
  }
}

document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("fileInput").files[0];
  if (!file) return alert("Please select a file.");

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/api/files/upload", {
    method: "POST",
    body: formData
  });

  if (res.ok) {
    alert("✅ File uploaded successfully!");
    await loadFiles();
  } else {
    alert("❌ Failed to upload file.");
  }
});

async function deleteFile(filename) {
  if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

  const res = await fetch(`/api/files/delete/${filename}`, { method: "DELETE" });
  if (res.ok) {
    alert("🗑️ File deleted successfully!");
    await loadFiles();
  } else {
    alert("❌ Failed to delete file.");
  }
}

loadFiles();


let fileChart;

async function loadFileChart() {
  const res = await fetch("/api/files/stats");
  const stats = await res.json();

  const ctx = document.getElementById("fileChart").getContext("2d");
  if (fileChart) fileChart.destroy();

  fileChart = new Chart(ctx, {
  type: "pie",
  data: {
    labels: ["Images", "Documents", "Others"],
    datasets: [{
      data: [stats.images, stats.documents, stats.others],
      backgroundColor: ["#0d6efd", "#20c997", "#ffc107"],
      borderWidth: 1,
    }]
  },
    options: {
    responsive: true,
    maintainAspectRatio: false, // ✅ allows full control of height
    plugins: {
      legend: { position: "bottom", labels: { boxWidth: 20 } },
      title: {
        display: true,
        text: "Storage Usage (MB) by File Type",
        font: { size: 16 }
      }
    },
    layout: {
      padding: { top: 10, bottom: 10 }
    }
  }
});
}

// Load chart when page opens or after upload/delete
async function refreshFiles() {
  await loadFiles();
  await loadFileChart();
}

document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const file = document.getElementById("fileInput").files[0];
  if (!file) return alert("Please select a file.");

  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch("/api/files/upload", { method: "POST", body: formData });
  if (res.ok) {
    alert("✅ File uploaded successfully!");
    await refreshFiles();
  } else {
    alert("❌ Failed to upload file.");
  }
});

async function deleteFile(filename) {
  if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;
  const res = await fetch(`/api/files/delete/${filename}`, { method: "DELETE" });
  if (res.ok) {
    alert("🗑️ File deleted successfully!");
    await refreshFiles();
  } else {
    alert("❌ Failed to delete file.");
  }
}

refreshFiles();

// 🖼️ Handle Image Preview Click
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("preview-img")) {
    const imgSrc = e.target.getAttribute("src");
    const modalImg = document.getElementById("previewImage");
    modalImg.src = imgSrc;
    const modal = new bootstrap.Modal(document.getElementById("imagePreviewModal"));
    modal.show();
  }
});

