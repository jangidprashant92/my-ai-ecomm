import MainLayout from "@/layouts/MainLayout";
import { ChatPage } from "@/pages/Chat";
import Dashboard from "@/pages/Dashboard";
import { createBrowserRouter } from "react-router";

const router = createBrowserRouter([
  {
    path: "/",
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <Dashboard />,
      },
      {
        path: "dashboard",
        element: <Dashboard />,
      },
      {
        path: "chat/:conversationId",
        element: <ChatPage />,
      },
    ],
  },
]);
export default router;
