import { Thread } from "@/components/assistant-ui/elements/thread.aui";
import { Skeleton } from "@/components/ui/skeleton";
import { useChat } from "@/context/ChatContext";

export function ChatPage() {
  const { isLoading } = useChat();
  if (isLoading) {
    return (
      <div className="flex h-full w-full flex-col justify-end gap-4 p-6">
        <div className="space-y-4">
          <Skeleton className="h-10 w-2/5 rounded-lg" />
          <Skeleton className="h-16 w-3/5 rounded-lg" />
          <Skeleton className="h-12 w-1/3 rounded-lg" />
        </div>
        <Skeleton className="h-14 w-full rounded-lg" />
      </div>
    );
  }

  return <Thread />;
}
