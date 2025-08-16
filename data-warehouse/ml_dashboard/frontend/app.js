const lossCtx = document.getElementById("lossChart").getContext("2d");
const accuracyCtx = document.getElementById("accuracyChart").getContext("2d");

const lossChart = new Chart(lossCtx, {
  type: "line",
  data: {
    labels: [],
    datasets: [
      {
        label: "Training Loss",
        data: [],
        borderColor: "#e74c3c",
        fill: false,
      },
      {
        label: "Validation Loss",
        data: [],
        borderColor: "#3498db",
        fill: false,
      },
    ],
  },
  options: { responsive: true, animation: false },
});

const accuracyChart = new Chart(accuracyCtx, {
  type: "line",
  data: {
    labels: [],
    datasets: [{
      label: "Accuracy (%)",
      data: [],
      borderColor: "#2ecc71",
      fill: false,
    }],
  },
  options: { responsive: true, animation: false },
});

function updateProgressBar(epoch, maxEpoch = 50) {
  const percent = Math.min(100, (epoch / maxEpoch) * 100);
  document.getElementById("progressFill").style.width = percent + "%";
}

function appendLog(message) {
  const logs = document.getElementById("logs");
  const entry = document.createElement("li");
  entry.textContent = message;
  logs.appendChild(entry);
  logs.scrollTop = logs.scrollHeight;
}

function downloadJSON() {
  const metrics = {
    epochs: lossChart.data.labels,
    trainingLoss: lossChart.data.datasets[0].data,
    validationLoss: lossChart.data.datasets[1].data,
    accuracy: accuracyChart.data.datasets[0].data
  };

  const dataStr = JSON.stringify(metrics, null, 2);
  const blob = new Blob([dataStr], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "training_metrics.json";
  link.click();
}

function downloadCSV() {
  const rows = [["Epoch", "Training Loss", "Validation Loss", "Accuracy"]];
  const len = lossChart.data.labels.length;

  for (let i = 0; i < len; i++) {
    rows.push([
      lossChart.data.labels[i],
      lossChart.data.datasets[0].data[i],
      lossChart.data.datasets[1].data[i],
      accuracyChart.data.datasets[0].data[i],
    ]);
  }

  const csv = rows.map(r => r.join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "training_metrics.csv";
  link.click();
}

// WebSocket connection
const ws = new WebSocket("ws://localhost:8000/ws/metrics");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  const label = "Epoch " + data.epoch;
  lossChart.data.labels.push(label);
  accuracyChart.data.labels.push(label);

  lossChart.data.datasets[0].data.push(data.train_loss);
  lossChart.data.datasets[1].data.push(data.val_loss);
  accuracyChart.data.datasets[0].data.push(data.accuracy);

  lossChart.update();
  accuracyChart.update();

  updateProgressBar(data.epoch);
  appendLog(`Epoch ${data.epoch}: Loss ${data.train_loss}, Accuracy ${data.accuracy}%`);
};
