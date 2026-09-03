import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 10000,
  headers: {
    //'Authorization': 'token <your-token-here>
  },
});
export default api;
