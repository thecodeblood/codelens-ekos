import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const executeQuery = async (query) => {
  try {
    const response = await api.post('/query', { query });
    return response.data;
  } catch (error) {
    console.error('Error executing query:', error);
    throw error;
  }
};

export const getModelQuality = async () => {
  try {
    const response = await api.get('/model/quality');
    return response.data;
  } catch (error) {
    console.error('Error getting model quality:', error);
    throw error;
  }
};

export default api;
