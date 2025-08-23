// sensorLineChart.js
import { fetchData, generateColors } from './chartUtils.js';

let sensorLineChart;

export async function renderSensorLineChart() {
  try {
    const data = await fetchData("/api/admin/sensor-timeline");
    const ctx = document.getElementById("sensorLineChart").getContext("2d");

    const labels = data.timestamps;
    let datasets;

    if (Array.isArray(data.datasets)) {
      const colors = generateColors(data.datasets.length);
      datasets = data.datasets.map((set, index) => ({
        label: set.label,
        data: set.values,
        borderColor: colors[index],
        fill: false
      }));
    } else {
      datasets = [{
        label: 'Sensor Value',
        data: data.values,
        borderColor: '#3498db',
        fill: false
      }];
    }

    if (sensorLineChart) {
      sensorLineChart.destroy();
    }

    sensorLineChart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        plugins: {
          title: {
            display: true,
            text: 'Sensor Timeline'
          }
        },
        scales: {
          x: {
            display: true,
            title: { display: true, text: 'Time' }
          },
          y: {
            display: true,
            title: { display: true, text: 'Value' },
            beginAtZero: true
          }
        }
      }
    });
  } catch (error) {
    console.error('Line chart error:', error);
  }
}
