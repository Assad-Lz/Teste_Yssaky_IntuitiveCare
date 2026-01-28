// src/services/api.js

import axios from 'axios';

/**
 * Axios instance configured with the base URL for the backend API.
 * This instance is used to make HTTP requests to the Python backend server.
 */
const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api',
});

export default {
  /**
   * Fetches a paginated list of health insurance providers (operadoras) with optional search.
   * @param {number} [page=1] - The page number for pagination.
   * @param {string} [search=''] - The search query to filter providers.
   * @returns {Promise} Axios response promise containing the list of providers.
   */
  getOperadoras(page = 1, search = '') {
    return api.get('/operadoras', {
      params: { page, limit: 10, search },
    });
  },

  /**
   * Fetches detailed information for a specific health insurance provider by CNPJ.
   * @param {string} cnpj - The CNPJ (Brazilian company identifier) of the provider.
   * @returns {Promise} Axios response promise containing the provider details.
   */
  getOperadoraDetails(cnpj) {
    return api.get(`/operadoras/${cnpj}`);
  },

  /**
   * Fetches expense data for a specific health insurance provider.
   * @param {string} cnpj - The CNPJ of the provider.
   * @returns {Promise} Axios response promise containing the expense data.
   */
  getOperadoraExpenses(cnpj) {
    return api.get(`/operadoras/${cnpj}/despesas`);
  },

  /**
   * Fetches general statistics data, typically used for charts and visualizations.
   * @returns {Promise} Axios response promise containing the statistics data.
   */
  getEstatisticas() {
    return api.get('/estatisticas');
  },
};
