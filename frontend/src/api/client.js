import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 90000, // 90 second timeout buffering Render cold starts
  headers: {
    'Content-Type': 'application/json',
  },
});

export default api;
