import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
});

export async function analyzeDataset(file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await client.post('/analyze-dataset', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return res.data;
}

export async function explainDecision(decisionId, language = 'hi') {
  const res = await client.post('/explain-decision', {
    decision_id: decisionId,
    language,
  });
  return res.data;
}

export async function getAuditHistory(params = {}) {
  const res = await client.get('/audit-history', { params });
  return res.data;
}

export async function healthCheck() {
  const res = await client.get('/health');
  return res.data;
}

export default client;
