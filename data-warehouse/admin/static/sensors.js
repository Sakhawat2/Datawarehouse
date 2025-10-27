//────────────────────────────────────────────
// Sensors Page Script (Admin)
//────────────────────────────────────────────



const sensorSelect = document.getElementById("sensorSelect");
const newSensorName = document.getElementById("newSensorName");
const sensorList = document.getElementById("sensorList");
const ctx = document.getElementById("sensorChart").getContext("2d");
let chart;

//────────────────────────────────────────────
// Load sensors into dropdowns
//────────────────────────────────────────────
async function loadSensors() {
  const res = await apiFetch("/api/sensors");
  const sensors = await res.json();

  // Dropdown
  sensorSelect.innerHTML = "";
  sensors.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.id;
    opt.textContent = s.name;
    sensorSelect.appendChild(opt);
  });

  // Datalist
  sensorList.innerHTML = "";
  sensors.forEach(s => {
    const opt = document.createElement("option");
    opt.value = s.name;
    sensorList.appendChild(opt);
  });

  if (sensors.length > 0) {
    sensorSelect.value = sensors[0].id;
    await loadSensorData(sensors[0].id);
    await loadAllSensorData();
  }
}

//────────────────────────────────────────────
// Load single sensor chart + stats
//────────────────────────────────────────────
async function loadSensorData(sensorId) {
  const res = await apiFetch(`/api/sensors/${sensorId}/readings`);
  if (!res.ok) return;

  const readings = await res.json();
  if (!readings || readings.length === 0) return;

  const timestamps = readings.map(r => r.ts);
  const values = readings.map(r => r.value);

  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  document.getElementById("latest-value").textContent = values.at(-1).toFixed(2);
  document.getElementById("avg-value").textContent = avg.toFixed(2);
  document.getElementById("min-value").textContent = Math.min(...values).toFixed(2);
  document.getElementById("max-value").textContent = Math.max(...values).toFixed(2);
  document.getElementById("total-records").textContent = values.length;

  if (chart) chart.destroy();
  chart = new Chart(ctx, {
    type: "line",
    data: {
      labels: timestamps,
      datasets: [
        {
          label: "Sensor Value",
          data: values,
          borderColor: "#0d6efd",
          fill: false,
          tension: 0.3,
          pointRadius: 2,
        },
      ],
    },
    options: {
      responsive: true,
      scales: {
        x: { title: { display: true, text: "Timestamp" } },
        y: { title: { display: true, text: "Value" } },
      },
    },
  });
}

//────────────────────────────────────────────
// Load all sensor readings table
//────────────────────────────────────────────
async function loadAllSensorData() {
  const tableBody = document.getElementById("sensorTableBody");
  tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">Loading...</td></tr>`;

  try {
    const res = await apiFetch("/api/sensors/all-readings");
    const data = await res.json();

    if (!Array.isArray(data) || data.length === 0) {
      tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No data found</td></tr>`;
      return;
    }

    tableBody.innerHTML = "";
    data.forEach(row => {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td>${row.sensor_name || "-"}</td>
        <td>${row.start_time || "-"}</td>
        <td>${row.end_time || "-"}</td>
        <td>${row.value ?? "-"}</td>
        <td>${row.unit || "-"}</td>
        <td>
          <button class="btn btn-sm btn-warning edit-btn" 
            data-id="${row.id}" 
            data-value="${row.value}" 
            data-unit="${row.unit}">
            ✏️ Edit
          </button>
          <button class="btn btn-sm btn-danger delete-btn" data-id="${row.id}">
            🗑️ Delete
          </button>
        </td>
      `;
      tableBody.appendChild(tr);
    });
  } catch (err) {
    console.error("Error loading sensor data:", err);
    tableBody.innerHTML = `<tr><td colspan="6" class="text-center text-danger">Error loading data</td></tr>`;
  }
}

//────────────────────────────────────────────
// Add new reading
//────────────────────────────────────────────
document.getElementById("addReadingForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const sensorName = newSensorName.value.trim();
  if (!sensorName) {
    alert("⚠️ Please enter or select a sensor name.");
    return;
  }

  const formData = new FormData();
  formData.append("sensor_name", sensorName);
  formData.append("value", parseFloat(document.getElementById("newValue").value));
  formData.append("unit", document.getElementById("newUnit").value);
  formData.append("ts", document.getElementById("newTimestamp").value);

  const res = await apiFetch("/api/sensors/add", { method: "POST", body: formData });

  if (res.ok) {
    alert("✅ New reading added!");
    await loadSensors();
    await loadAllSensorData();
  } else {
    alert("❌ Failed to add reading.");
  }
});

//────────────────────────────────────────────
// Delete reading
//────────────────────────────────────────────
document.addEventListener("click", async (e) => {
  if (e.target.classList.contains("delete-btn")) {
    const id = e.target.dataset.id;
    if (!confirm("🗑️ Delete this reading?")) return;
    const res = await apiFetch(`/api/sensors/delete/${id}`, { method: "DELETE" });
    if (res.ok) {
      alert("✅ Deleted successfully");
      await loadAllSensorData();
    } else {
      alert("❌ Failed to delete");
    }
  }
});

//────────────────────────────────────────────
// Event listeners + init
//────────────────────────────────────────────
sensorSelect.addEventListener("change", e => loadSensorData(e.target.value));
document.getElementById("refreshBtn").addEventListener("click", () => loadSensorData(sensorSelect.value));

loadSensors();
