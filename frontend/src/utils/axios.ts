import axios from "axios";

const api = axios.create({
  baseURL: process.env.CASINO_API_URL,
  timeout: 10000,
  headers: {
    //'Authorization': 'token <your-token-here>
  },
});

export default api;