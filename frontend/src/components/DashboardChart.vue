<template>
  <div class="chart-container">
    <h3>Despesas por UF (Top 5)</h3>
    <Bar v-if="loaded" :data="chartData" :options="chartOptions" />
    <p v-else>Carregando gráfico...</p>
  </div>
</template>

<script>
import { Bar } from 'vue-chartjs';
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from 'chart.js';
import api from '../services/api';

ChartJS.register(
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
);

export default {
  name: 'DashboardChart',
  components: { Bar },
  data() {
    return {
      loaded: false,
      chartData: null,
      chartOptions: {
        responsive: true,
        maintainAspectRatio: false,
      },
    };
  },
  async mounted() {
    try {
      const response = await api.getEstatisticas();
      // O backend retorna: { despesas_por_uf: [{ uf: 'SP', total: 5000 }, ...] }
      const dadosUF = response.data.despesas_por_uf;

      this.chartData = {
        // CORREÇÃO AQUI: Use .uf (minúsculo)
        labels: dadosUF.map((item) => item.uf),
        datasets: [
          {
            label: 'Total de Despesas (R$)',
            backgroundColor: '#42b883',
            // CORREÇÃO AQUI: Use .total (alias definido na query SQL)
            data: dadosUF.map((item) => item.total),
          },
        ],
      };
      this.loaded = true;
    } catch (error) {
      console.error('Erro ao carregar gráfico:', error);
    }
  },
};
</script>

<style scoped>
.chart-container {
  height: 300px;
  background: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
}
</style>
