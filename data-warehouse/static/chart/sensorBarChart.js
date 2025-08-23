import { fetchData, generateColors } from './chartUtils.js';

export function renderSensorBarChart() {
  fetchData("/api/admin/sensor-activity").then(data => {
    const ctx = document.getElementById("sensorBarChart").getContext("2d");

    let labels, datasets;

    if (Array.isArray(data.datasets)) {
      labels = data.labels;
      const colors = generateColors(data.datasets.length);
      datasets = data.datasets.map((set, index) => ({
        label: set.label,
        data: set.values,
        backgroundColor: colors[index]
      }));
    } else {
      labels = Object.keys(data);
      datasets = [{
        label: 'Activity Count',
        data: Object.values(data),
        backgroundColor: '#2ecc71'
      }];
    }

    new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  });
}
