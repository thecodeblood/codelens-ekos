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

export const getSources = async () => {
  const response = await api.get('/sources');
  return response.data;
};

export const addSource = async (type, uri, name) => {
  const response = await api.post('/sources', { type, uri, name });
  return response.data;
};

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/sources/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const triggerIngestion = async (sourceId) => {
  const response = await api.post(`/sources/${sourceId}/ingest`);
  return response.data;
};

export default api;
