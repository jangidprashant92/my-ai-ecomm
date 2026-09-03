import { RouterProvider } from "react-router/internal/react-server-client";
import "./App.css";
import QueryProvider from "./lib/providers/query-provider";
import router from "./routes";

function App() {
  return (
    <QueryProvider>
      <RouterProvider router={router} />
    </QueryProvider>
  );
}

export default App;
