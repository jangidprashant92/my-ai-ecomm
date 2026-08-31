import { useEffect, useState } from "react";

import { MessageSquare, Plus } from "lucide-react";

import { getConversations, type Conversation } from "@/api/conversations";

type ConversationSidebarProps = {
  conversationId: string | null;

  onSelectConversation: (conversationId: string) => void;

  onNewConversation: () => void;
};

export function ConversationSidebar({
  conversationId,
  onSelectConversation,
  onNewConversation,
}: ConversationSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadConversations() {
      try {
        const data = await getConversations();

        setConversations(data.data);
      } catch (error) {
        console.error("Failed to load conversations:", error);
      } finally {
        setLoading(false);
      }
    }

    loadConversations();
  }, []);

  return (
    <aside className="flex h-screen w-72 flex-col border-r bg-background">
      {/* HEADER */}

      <div className="border-b p-4">
        <button
          onClick={onNewConversation}
          className="
            flex
            w-full
            items-center
            justify-center
            gap-2
            rounded-lg
            border
            px-4
            py-2
            text-sm
            font-medium
            hover:bg-muted
          "
        >
          <Plus className="h-4 w-4" />
          New Chat
        </button>
      </div>

      {/* CONVERSATIONS */}

      <div className="flex-1 overflow-y-auto p-2">
        {loading && (
          <p className="p-3 text-sm text-muted-foreground">
            Loading conversations...
          </p>
        )}

        {!loading && conversations.length === 0 && (
          <p className="p-3 text-sm text-muted-foreground">
            No conversations yet.
          </p>
        )}

        {conversations.map((conversation) => (
          <button
            key={conversation.conversation_id}
            onClick={() => onSelectConversation(conversation.conversation_id)}
            className={`
                mb-1
                flex
                w-full
                items-center
                gap-3
                rounded-lg
                px-3
                py-3
                text-left
                text-sm
                transition-colors

                ${
                  conversationId === conversation.conversation_id
                    ? "bg-muted"
                    : "hover:bg-muted"
                }
              `}
          >
            <MessageSquare
              className="
                  h-4
                  w-4
                  shrink-0
                "
            />

            <span className="truncate">
              {conversation.title || "New Conversation"}
            </span>
          </button>
        ))}
      </div>
    </aside>
  );
}
