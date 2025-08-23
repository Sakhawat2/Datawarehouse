// main.js
import { renderSensorBarChart } from './sensorBarChart.js';
import { renderSensorLineChart } from './sensorLineChart.js';
import { renderPieChart } from './sensorPieChart.js';


window.onload = () => {
  loadSensorData();
  renderSensorLineChart(); // 👈 This is crucial
};

// 🚀 Initialize all charts after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  renderSensorBarChart();
  renderSensorLineChart();
  renderPieChart();
});
