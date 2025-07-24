import axios from 'axios';
const apiClient = axios.create({
  baseURL: 'http://127.0.0.1:5000', // バックエンドサーバーのアドレス
  headers: {
    'Content-Type': 'application/json',
  },
});
export default {
  evaluateStock(data) {
    return apiClient.post('/api/evaluate', data);
  },
};
