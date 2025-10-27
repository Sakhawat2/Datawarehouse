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
// Chart.js helper
// ─────────────────────────────────────────────
function makeBar(ctx, title) {
  return new Chart(ctx, {
    type: 'bar',
    data: { labels: [], datasets: [{ label: title, data: [], backgroundColor: '#0d6efd', borderRadius: 6 }] },
    options: {
      responsive: true,
      scales: { y: { beginAtZero: true } },
      plugins: {
        tooltip: { enabled: true },
        legend: { display: false },
      },
      animation: { duration: 1200, easing: 'easeOutQuart' }
    }
  });
}

// ─────────────────────────────────────────────
// Update functions
// ─────────────────────────────────────────────
async function updateStorageDisplay() {
  const res = await fetch('/api/admin/storage-usage');
  const data = await res.json();
  document.getElementById('storage-total').textContent =
    data.total_storage_mb ? data.total_storage_mb.toFixed(2) : '0.00';

  const ctx = document.getElementById('storageChart').getContext('2d');
  new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: Object.keys(data.details),
      datasets: [{
        data: Object.values(data.details),
        backgroundColor: ['#0d6efd', '#dc3545', '#198754']
      }]
    },
    options: {
      plugins: {
        legend: { position: 'bottom' },
        title: { display: true, text: 'Storage Breakdown (MB)' },
        tooltip: { enabled: true }
      }
    }
  });
}

async function updateSensorChart(chart) {
  const res = await fetch('/api/admin/sensor-count');
  const data = await res.json();
  chart.data.labels = Object.keys(data);
  chart.data.datasets[0].data = Object.values(data);
  chart.update();
  document.getElementById('sensor-total').textContent = Object.keys(data).length;
}

async function updateVideoChart(chart) {
  const res = await fetch('/api/admin/video-storage');
  const data = await res.json();
  chart.data.labels = Object.keys(data.files);
  chart.data.datasets[0].data = Object.values(data.files);
  chart.update();
  document.getElementById('video-total').textContent = Object.keys(data.files).length;
}

// Fake average reading just to show metric card
function updateAvgReading() {
  const random = (Math.random() * 100).toFixed(1);
  document.getElementById('avg-reading').textContent = random;
}

// Update timestamp
function updateTimestamp() {
  const ts = new Date().toLocaleTimeString();
  document.getElementById('last-updated').textContent = `Last updated: ${ts}`;
}

// ─────────────────────────────────────────────
// Main initialization
// ─────────────────────────────────────────────
(async function () {
  await updateStorageDisplay();
  const sensorChart = makeBar(document.getElementById('sensorCountBarChart').getContext('2d'), 'Sensor Count');
  const videoChart = makeBar(document.getElementById('videoCountBarChart').getContext('2d'), 'Size (MB)');
  await updateSensorChart(sensorChart);
  await updateVideoChart(videoChart);
  updateAvgReading();
  updateTimestamp();
  setInterval(() => {
    updateSensorChart(sensorChart);
    updateVideoChart(videoChart);
    updateAvgReading();
    updateTimestamp();
  }, 15000);
})();

// ─────────────────────────────────────────────
// Dark mode toggle
// ─────────────────────────────────────────────
const toggleBtn = document.getElementById('themeToggle');
toggleBtn.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme');
  if (current === 'dark') {
    document.documentElement.removeAttribute('data-theme');
    toggleBtn.textContent = '🌙 Dark Mode';
  } else {
    document.documentElement.setAttribute('data-theme', 'dark');
    toggleBtn.textContent = '☀️ Light Mode';
  }
});
