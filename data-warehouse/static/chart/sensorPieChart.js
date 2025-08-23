import { fetchData } from './chartUtils.js';

export function renderSensorPieChart() {
  fetchData("/api/admin/sensor-distribution").then(data => {
    const ctx = document.getElementById("sensorPieChart").getContext("2d");
    new Chart(ctx, {
      type: 'pie',
      data: {
        labels: Object.keys(data),
        datasets: [{
          data: Object.values(data),
          backgroundColor: ['#3498db', '#e67e22', '#9b59b6', '#2ecc71', '#f1c40f'],
        }]
      },
      options: {
        plugins: { legend: { position: 'bottom' } }
      }
    });
  });
}
