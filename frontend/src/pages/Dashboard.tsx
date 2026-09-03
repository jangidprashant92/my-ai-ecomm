import { Thread } from "@/components/assistant-ui/elements/thread.aui";
import { useAui } from "@assistant-ui/react";
import { useEffect } from "react";

function Dashboard() {
  const aui = useAui();

  useEffect(() => {
    // Reset or switch to an empty/new thread when visiting /dashboard
    aui.threads.switchToThread("main");
    console.log(
      "Dashboard: switched to new thread with conversationId:",
      "123e4567-e89b-12d3-a456-426614174000",
    );
  }, [aui]);

  // Optional: Listen for thread creation to navigate to /chat/:conversationId
  // Many adapters emit an event or update `runtime.threads.main.threadId`

  return <Thread />;
}
export default Dashboard;
