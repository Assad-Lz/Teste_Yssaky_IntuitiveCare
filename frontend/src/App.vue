<template>
  <div class="app-container">
    <header>
      <h1>Intuitive Care - Busca de Operadoras</h1>
    </header>

    <main v-if="!selectedOperadora">
      <DashboardChart />

      <div class="search-bar">
        <input
          v-model="searchQuery"
          @input="handleSearch"
          placeholder="Buscar por Razão Social..."
          class="search-input"
        />
      </div>

      <div class="table-container">
        <table>
          <thead>
            <tr>
              <th>Registro ANS</th>
              <th>CNPJ</th>
              <th>Razão Social</th>
              <th>UF</th>
              <th>Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="op in operadoras" :key="op.registro_ans">
              <td>{{ op.registro_ans }}</td>
              <td>{{ op.cnpj }}</td>
              <td>{{ op.razao_social }}</td>
              <td>{{ op.uf }}</td>
              <td>
                <button
                  class="btn-details"
                  @click="viewDetails(op.registro_ans)"
                >
                  Ver Detalhes
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="pagination">
        <button :disabled="page === 1" @click="changePage(page - 1)">
          Anterior
        </button>
        <span>Página {{ page }} de {{ totalPages }}</span>
        <button :disabled="page === totalPages" @click="changePage(page + 1)">
          Próxima
        </button>
      </div>
    </main>

    <div v-else class="details-view">
      <button class="btn-back" @click="selectedOperadora = null">
        ← Voltar para Lista
      </button>

      <div class="card">
        <h2>{{ selectedOperadora.razao_social }}</h2>
        <div class="info-grid">
          <p><strong>CNPJ:</strong> {{ selectedOperadora.cnpj }}</p>
          <p>
            <strong>Registro ANS:</strong> {{ selectedOperadora.registro_ans }}
          </p>
          <p><strong>UF:</strong> {{ selectedOperadora.uf }}</p>
          <p><strong>Modalidade:</strong> {{ selectedOperadora.modalidade }}</p>
        </div>
      </div>

      <div class="card">
        <h3>Histórico de Despesas</h3>
        <table v-if="expenses.length">
          <thead>
            <tr>
              <th>Ano/Trimestre</th>
              <th>Descrição</th>
              <th>Valor (R$)</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="exp in expenses" :key="exp.id">
              <td>{{ exp.ano }}/{{ exp.trimestre }}</td>
              <td>{{ exp.descricao }}</td>
              <td class="money">{{ formatCurrency(exp.valor_despesa) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-else>Nenhuma despesa registrada para esta operadora.</p>
      </div>
    </div>
  </div>
</template>

<script>
import api from './services/api';
import DashboardChart from './components/DashboardChart.vue';

export default {
  components: { DashboardChart },
  data() {
    return {
      operadoras: [],
      searchQuery: '',
      page: 1,
      totalPages: 1,
      selectedOperadora: null,
      expenses: [],
      timeout: null,
    };
  },
  methods: {
    async fetchOperadoras() {
      try {
        const response = await api.getOperadoras(this.page, this.searchQuery);
        this.operadoras = response.data.data;

        const limit = 10;
        const total = response.data.meta.total;
        this.totalPages = Math.ceil(total / limit) || 1;
      } catch (error) {
        console.error('Erro API:', error);
      }
    },
    handleSearch() {
      clearTimeout(this.timeout);
      this.timeout = setTimeout(() => {
        this.page = 1;
        this.fetchOperadoras();
      }, 500);
    },
    changePage(newPage) {
      if (newPage >= 1 && newPage <= this.totalPages) {
        this.page = newPage;
        this.fetchOperadoras();
      }
    },
    async viewDetails(id) {
      const op = this.operadoras.find((o) => o.registro_ans === id);
      if (op) {
        this.selectedOperadora = op;
        // Agora buscamos as despesas no backend!
        try {
          const expResponse = await api.getOperadoraExpenses(id);
          this.expenses = expResponse.data;
        } catch (error) {
          console.error('Erro ao buscar despesas:', error);
          this.expenses = [];
        }
      }
    },
    formatCurrency(value) {
      if (!value) return 'R$ 0,00';
      return new Intl.NumberFormat('pt-BR', {
        style: 'currency',
        currency: 'BRL',
      }).format(value);
    },
  },
  mounted() {
    this.fetchOperadoras();
  },
};
</script>

<style>
/* Seus estilos originais mantidos */
body {
  font-family: Arial, sans-serif;
  background-color: #f4f4f9;
  margin: 0;
  padding: 20px;
}
.app-container {
  max-width: 1000px;
  margin: 0 auto;
}
header {
  margin-bottom: 20px;
  text-align: center;
  color: #333;
}
.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
table {
  width: 100%;
  border-collapse: collapse;
}
th,
td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #ddd;
}
th {
  background-color: #42b883;
  color: white;
}
tr:hover {
  background-color: #f1f1f1;
}
.search-input {
  width: 100%;
  padding: 10px;
  margin-bottom: 20px;
  border: 1px solid #ddd;
  border-radius: 4px;
  box-sizing: border-box;
}
button {
  padding: 8px 12px;
  border: none;
  cursor: pointer;
  border-radius: 4px;
}
.btn-details {
  background-color: #35495e;
  color: white;
}
.btn-back {
  background-color: #666;
  color: white;
  margin-bottom: 20px;
}
.pagination {
  margin-top: 20px;
  display: flex;
  justify-content: center;
  gap: 15px;
  align-items: center;
}
.pagination button {
  background-color: #42b883;
  color: white;
}
.pagination button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}
.card {
  background: white;
  padding: 20px;
  margin-bottom: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
.money {
  font-family: monospace;
  font-weight: bold;
  color: #d32f2f;
}
</style>
