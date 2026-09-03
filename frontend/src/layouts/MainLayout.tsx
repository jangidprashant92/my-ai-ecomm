import { ThreadListSidebar } from "@/components/assistant-ui/threadlist-sidebar";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import ChatProvider, { useChat } from "@/context/ChatContext";
import { AssistantRuntimeProvider } from "@assistant-ui/react";
import { Outlet } from "react-router";

function ChatRuntimeBridge({ children }: { children: React.ReactNode }) {
  const { runtime } = useChat();
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {children}
    </AssistantRuntimeProvider>
  );
}

function MainLayout() {
  return (
    <ChatProvider>
      <ChatRuntimeBridge>
        <SidebarProvider>
          <div className="flex h-dvh w-full pr-0.5">
            <ThreadListSidebar />
            <SidebarInset>
              <header className="flex h-16 shrink-0 items-center gap-2 border-b px-4">
                <SidebarTrigger />
                <Separator orientation="vertical" className="mr-2 h-4" />
              </header>
              <div className="flex-1 overflow-hidden">
                <Outlet />
              </div>
            </SidebarInset>
          </div>
        </SidebarProvider>
      </ChatRuntimeBridge>
    </ChatProvider>
  );
}

export default MainLayout;
