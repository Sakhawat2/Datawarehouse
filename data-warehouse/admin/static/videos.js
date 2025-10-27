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


// 
// videos.js - Admin Video Management
// ─────────────────────────────────────────────
const videoTableBody = document.getElementById("videoTableBody");
const ctx = document.getElementById("videoChart").getContext("2d");
const previewVideo = document.getElementById("previewVideo");
let chart;

// ✅ Load all videos
async function loadVideos() {
  videoTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Loading...</td></tr>`;

  try {
    const res = await fetch("/api/videos");
    const videos = await res.json();

    if (!Array.isArray(videos) || videos.length === 0) {
      videoTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No videos found</td></tr>`;
      return;
    }

    videoTableBody.innerHTML = "";
    videos.forEach(v => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${v.name}</td>
        <td>${v.size_mb.toFixed(2)}</td>
        <td>
          <button class="btn btn-sm btn-primary preview-btn" data-name="${v.name}">
            ▶ Watch
          </button>
        </td>
        <td>
          <a href="/api/videos/download/${v.name}" class="btn btn-sm btn-secondary">⬇ Download</a>
        </td>
        <td>
          <button class="btn btn-sm btn-danger delete-btn" data-name="${v.name}">🗑 Delete</button>
        </td>
      `;
      videoTableBody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading videos:", err);
    videoTableBody.innerHTML = `<tr><td colspan="5" class="text-center text-danger">Error loading videos</td></tr>`;
  }
}

// 🎥 Handle Watch (Preview)
document.addEventListener("click", async (e) => {
  if (e.target.classList.contains("preview-btn")) {
    const name = e.target.dataset.name;
    const videoSrc = `/api/videos/watch/${name}`;
    previewVideo.src = videoSrc;
    new bootstrap.Modal(document.getElementById("videoModal")).show();
  }

  // Delete button
  if (e.target.classList.contains("delete-btn")) {
    const name = e.target.dataset.name;
    if (!confirm(`Are you sure you want to delete "${name}"?`)) return;

    const res = await fetch(`/api/videos/delete/${name}`, { method: "DELETE" });
    if (res.ok) {
      alert("✅ Video deleted successfully");
      await loadVideos();
      await loadVideoChart();
    } else {
      alert("❌ Failed to delete video");
    }
  }
});

// ✅ Handle video upload
document.getElementById("uploadForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const fileInput = document.getElementById("videoFile");
  if (!fileInput.files.length) {
    alert("⚠️ Please choose a file first.");
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  const res = await fetch("/api/videos/upload", {
    method: "POST",
    body: formData
  });

  if (res.ok) {
    alert("✅ Video uploaded successfully!");
    fileInput.value = "";
    await loadVideos();
    await loadVideoChart();
  } else {
    alert("❌ Failed to upload video.");
  }
});

// ✅ Load video analytics chart
async function loadVideoChart() {
  try {
    const res = await fetch("/api/admin/video-storage");
    const data = await res.json();

    const labels = Object.keys(data.buckets);
    const counts = Object.values(data.buckets);

    if (chart) chart.destroy();
    chart = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [{
          label: "Number of Videos",
          data: counts,
          backgroundColor: ["#4e79a7", "#f28e2b", "#e15759"]
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: { title: { display: true, text: "File Size Range" } },
          y: { title: { display: true, text: "Video Count" } }
        }
      }
    });
  } catch (err) {
    console.error("Error loading video chart:", err);
  }
}

// ✅ Initialize page
(async () => {
  await loadVideos();
  await loadVideoChart();
})();
