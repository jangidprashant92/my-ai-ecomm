// src/context/ChatContext.tsx
import type { IMessage, IRawBackendMessage } from "@/interfaces";
import { streamChat } from "@/services/chat";
import messagesService from "@/services/messages";
import {
  useExternalStoreRuntime,
  type AppendMessage,
  type AssistantRuntime,
  type TextMessagePart,
  type ThreadMessageLike,
} from "@assistant-ui/react";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useLocation, useParams } from "react-router";

interface ChatContextValue {
  runtime: AssistantRuntime;
  messages: IMessage[];
  isLoading: boolean;
  isRunning: boolean;
  conversationId?: string;
}

const ChatContext = createContext<ChatContextValue | null>(null);

// Type guard using TextMessagePart
function isTextMessagePart(part: unknown): part is TextMessagePart {
  return (
    typeof part === "object" &&
    part !== null &&
    "type" in part &&
    (part as { type: string }).type === "text"
  );
}

function normalizeContent(
  rawContent: IRawBackendMessage["content"],
): ThreadMessageLike["content"] {
  if (typeof rawContent === "string") {
    return [{ type: "text", text: rawContent }];
  }
  return rawContent;
}

const convertMessage = (message: IMessage): ThreadMessageLike => {
  if (message.role === "assistant") {
    return {
      id: message.message_id,
      role: "assistant",
      content: message.content,
      createdAt: message.createdAt ? new Date(message.createdAt) : new Date(),
      ...(message.status ? { status: message.status } : {}),
    };
  }

  // User and system messages MUST NOT have a status property
  return {
    id: message.message_id,
    role: message.role,
    content: message.content,
    createdAt: message.createdAt ? new Date(message.createdAt) : new Date(),
  };
};

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const location = useLocation();

  const [messages, setMessages] = useState<IMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState<boolean>(Boolean(conversationId));

  useEffect(() => {
    if (!conversationId) {
      queueMicrotask(() => {
        setMessages([]);
        setIsLoading(false);
        setIsRunning(false);
      });
      return;
    }

    let active = true;
    queueMicrotask(() => {
      setIsLoading(true);
    });

    async function fetchMessages() {
      try {
        const res = await messagesService.getMessages(conversationId!);
        if (active) {
          const rawItems: IRawBackendMessage[] = res.data.messages ?? [];

          const normalizedMessages: IMessage[] = rawItems.map((msg) => ({
            id: msg.message_id,
            message_id: msg.message_id,
            conversation_id: msg.conversation_id,
            parent_message_id: msg.parent_message_id,
            role: msg.role,
            content: normalizeContent(msg.content),
            createdAt: msg.created_at ? new Date(msg.created_at) : new Date(),
            status: msg.status ?? undefined,
          }));

          setMessages(normalizedMessages);
        }
      } catch (err) {
        console.error("Failed to load messages", err);
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    fetchMessages();
    return () => {
      active = false;
    };
  }, [conversationId, location.pathname]);

  const onNew = useCallback(
    async (message: AppendMessage) => {
      // Extract string text from parts
      const userText = message.content
        .filter(isTextMessagePart)
        .map((part) => part.text)
        .join("");

      if (!userText.trim()) return;

      const temporaryUserId = crypto.randomUUID();
      const temporaryAssistantId = crypto.randomUUID();
      const now = new Date();

      // FIX LINE 140: Add required reason: "stop"
      const optimisticUserMsg: IMessage = {
        id: temporaryUserId,
        message_id: temporaryUserId,
        conversation_id: conversationId ?? "",
        role: "user",
        content: message.content,
        createdAt: now,
        // status: { type: "complete", reason: "stop" },
      };

      const optimisticAssistantMsg: IMessage = {
        id: temporaryAssistantId,
        message_id: temporaryAssistantId,
        conversation_id: conversationId ?? "",
        role: "assistant",
        content: [{ type: "text", text: "" }],
        createdAt: now,
        status: { type: "running" },
      };

      setMessages((prev) => [
        ...prev,
        optimisticUserMsg,
        optimisticAssistantMsg,
      ]);
      setIsRunning(true);

      try {
        // FIX LINE 164: Pass userText (string) to match ChatStreamRequest
        await streamChat(
          {
            conversation_id: conversationId,
            message: userText,
          },
          ({ event, data }) => {
            if (event === "message_start") {
              const backendUserId = String(data.user_message_id);
              const backendAssistantId = String(data.assistant_message_id);

              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.message_id === temporaryUserId) {
                    return {
                      ...msg,
                      id: backendUserId,
                      message_id: backendUserId,
                    };
                  }
                  if (msg.message_id === temporaryAssistantId) {
                    return {
                      ...msg,
                      id: backendAssistantId,
                      message_id: backendAssistantId,
                    };
                  }
                  return msg;
                }),
              );
              return;
            }

            if (event === "token") {
              const token = String(data.content ?? "");
              const assistantId = String(data.assistant_message_id);

              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.message_id !== assistantId) return msg;

                  let textUpdated = false;
                  const currentParts = Array.isArray(msg.content)
                    ? msg.content
                    : [];

                  const updatedParts = currentParts.map((part) => {
                    if (!textUpdated && isTextMessagePart(part)) {
                      textUpdated = true;
                      return {
                        ...part,
                        text: part.text + token,
                      };
                    }
                    return part;
                  });

                  if (!textUpdated) {
                    updatedParts.push({ type: "text", text: token });
                  }

                  return {
                    ...msg,
                    content: updatedParts,
                  };
                }),
              );
              return;
            }

            if (event === "complete") {
              const assistantId = String(data.assistant_message_id);
              setMessages((prev) =>
                prev.map((msg) =>
                  msg.message_id === assistantId
                    ? { ...msg, status: { type: "complete", reason: "stop" } }
                    : msg,
                ),
              );
              setIsRunning(false);
            }

            if (event === "error") {
              setIsRunning(false);
            }
          },
        );
      } catch (error) {
        console.error("Streaming error:", error);
      } finally {
        setIsRunning(false);
      }
    },
    [conversationId],
  );

  const runtime = useExternalStoreRuntime({
    messages,
    convertMessage,
    isRunning,
    onNew,
  });

  return (
    <ChatContext.Provider
      value={{
        runtime,
        messages,
        isLoading,
        isRunning,
        conversationId,
      }}
    >
      {children}
    </ChatContext.Provider>
  );
};

// eslint-disable-next-line react-refresh/only-export-components
export const useChat = () => {
  const context = useContext(ChatContext);
  if (!context) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
};

export default ChatProvider;
