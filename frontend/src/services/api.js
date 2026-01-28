import axios from 'axios';

const api = axios.create({
  // Padronize para localhost para evitar problemas de CORS com o navegador
  baseURL: 'http://localhost:8000/api',
});

export default {
  getOperadoras(page = 1, search = '') {
    return api.get('/operadoras', {
      params: { page, limit: 10, search },
    });
  },

  // No SQL, buscamos pelo ID (Registro ANS), não mais pelo CNPJ
  getOperadoraDetails(id) {
    return api.get(`/operadoras/${id}`);
  },

  // Essa rota busca as despesas usando o Registro ANS
  getOperadoraExpenses(id) {
    return api.get(`/operadoras/${id}/despesas`);
  },

  getEstatisticas() {
    return api.get('/estatisticas');
  },
};
