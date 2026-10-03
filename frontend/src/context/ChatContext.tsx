// src/context/ChatContext.tsx
import type { IMessage, IRawBackendMessage } from "@/interfaces";
import type { HumanReviewPayload } from "@/interfaces/chat";
import {
  resumeHumanReviewStream,
  streamChat,
  type HumanReviewRequest,
} from "@/services/chat";
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
  useRef,
  useState,
  type ReactNode,
} from "react";
import { useLocation, useNavigate, useParams } from "react-router";

interface ChatContextValue {
  runtime: AssistantRuntime;
  messages: IMessage[];
  isLoading: boolean;
  isRunning: boolean;
  conversationId?: string;
  resumeHumanReview: (
    assistantMessageId: string,
    review: HumanReviewRequest,
  ) => Promise<void>;
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
      createdAt: message.createdAt ?? new Date(),

      ...(message.status ? { status: message.status } : {}),

      ...(message.hitl
        ? {
            metadata: {
              custom: {
                humanReview: message.hitl,
              },
            },
          }
        : {}),
    };
  }

  return {
    id: message.message_id,
    role: message.role,
    content: message.content,
    createdAt: message.createdAt ?? new Date(),
  };
};

export const ChatProvider = ({ children }: { children: ReactNode }) => {
  const { conversationId } = useParams<{ conversationId?: string }>();
  const location = useLocation();
  const navigate = useNavigate();

  const [messages, setMessages] = useState<IMessage[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [isLoading, setIsLoading] = useState<boolean>(Boolean(conversationId));

  const abortControllerRef = useRef<AbortController | null>(null);

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

          const normalizedMessages: IMessage[] = rawItems.map((msg) => {
            const isPendingHumanReview =
              msg.role === "assistant" &&
              msg.status?.type === "waiting_for_approval";

            return {
              id: msg.message_id,
              message_id: msg.message_id,
              conversation_id: msg.conversation_id,
              parent_message_id: msg.parent_message_id,
              role: msg.role as "user" | "assistant",
              content: normalizeContent(msg.content),
              createdAt: msg.created_at ? new Date(msg.created_at) : new Date(),

              ragSources: msg.rag_sources ?? [],

              ...(msg.role === "assistant" && msg.status
                ? {
                    status: isPendingHumanReview
                      ? {
                          type: "requires-action",
                          reason: "interrupt",
                        }
                      : {
                          type: msg.status.type,
                          reason: msg.status.reason ?? "stop",
                        },
                  }
                : {}),
            };
          });

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

  function extractStreamText(value: unknown): string {
    if (typeof value === "string") {
      return value;
    }

    if (value == null) {
      return "";
    }

    if (typeof value === "object") {
      const obj = value as Record<string, unknown>;

      // Backend format:
      // { type: "text", content: "hello" }
      if (typeof obj.content === "string") {
        return obj.content;
      }

      // Alternative format:
      // { type: "text", text: "hello" }
      if (typeof obj.text === "string") {
        return obj.text;
      }
    }

    return "";
  }

  const resumeHumanReview = useCallback(
    async (assistantMessageId: string, review: HumanReviewRequest) => {
      if (!conversationId) {
        throw new Error("Conversation ID is required.");
      }

      const controller = new AbortController();

      abortControllerRef.current = controller;

      setIsRunning(true);

      setMessages((prev) =>
        prev.map((msg) =>
          msg.message_id === assistantMessageId
            ? {
                ...msg,
                content: [{ type: "text", text: "" }],
                status: { type: "running" },
                hitl: undefined,
              }
            : msg,
        ),
      );

      try {
        await resumeHumanReviewStream(
          conversationId,
          review,
          ({ event, data }) => {
            if (event === "token") {
              const token = extractStreamText(data.content);

              if (!token) {
                return;
              }

              const assistantId = String(
                data.assistant_message_id ?? assistantMessageId,
              );

              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.message_id !== assistantId) {
                    return msg;
                  }

                  const currentParts = Array.isArray(msg.content)
                    ? [...msg.content]
                    : [];

                  const textIndex = currentParts.findIndex(
                    (part) => part.type === "text",
                  );

                  if (textIndex !== -1) {
                    const part = currentParts[textIndex];

                    if (part.type === "text") {
                      currentParts[textIndex] = {
                        ...part,
                        text: part.text + token,
                      };
                    }
                  } else {
                    currentParts.push({
                      type: "text",
                      text: token,
                    });
                  }

                  return {
                    ...msg,
                    content: currentParts,
                  };
                }),
              );

              return;
            }

            if (event === "complete") {
              const assistantId = String(
                data.assistant_message_id ?? assistantMessageId,
              );

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.message_id === assistantId
                    ? {
                        ...msg,
                        status: {
                          type: "complete",
                          reason: "stop",
                        },
                        hitl: undefined,
                      }
                    : msg,
                ),
              );

              setIsRunning(false);
              return;
            }

            if (event === "error") {
              setIsRunning(false);
            }
          },
          controller.signal,
        );
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          console.log("Human review resume cancelled.");
          return;
        }
        console.error("HITL resume failed:", error);

        setMessages((prev) =>
          prev.map((msg) =>
            msg.message_id === assistantMessageId
              ? {
                  ...msg,
                  status: {
                    type: "incomplete",
                    reason: "error",
                    error:
                      error instanceof Error ? error.message : String(error),
                  },
                }
              : msg,
          ),
        );

        throw error;
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }
        setIsRunning(false);
      }
    },
    [conversationId],
  );

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
        ragSources: [],
      };

      const controller = new AbortController();

      abortControllerRef.current = controller;

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
            const token = extractStreamText(data.content);

            if (event === "message_start") {
              const backendConversationId = String(data.conversation_id);

              const backendUserId = String(data.user_message_id);

              const backendAssistantId = String(data.assistant_message_id);

              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.message_id === temporaryUserId) {
                    return {
                      ...msg,
                      id: backendUserId,
                      message_id: backendUserId,
                      conversation_id: backendConversationId,
                    };
                  }

                  if (msg.message_id === temporaryAssistantId) {
                    return {
                      ...msg,
                      id: backendAssistantId,
                      message_id: backendAssistantId,
                      conversation_id: backendConversationId,
                    };
                  }

                  return msg;
                }),
              );

              // First message from /dashboard
              if (!conversationId) {
                navigate(`/chat/${backendConversationId}`);
              }

              return;
            }

            if (event === "thinking") {
              console.log("Received thinking event:", token);

              const assistantId = String(data.assistant_message_id);

              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.message_id !== assistantId) return msg;

                  const currentParts = Array.isArray(msg.content)
                    ? [...msg.content]
                    : [];
                  const reasoningIndex = currentParts.findIndex(
                    (p) => p.type === "reasoning",
                  );

                  if (reasoningIndex !== -1) {
                    const existing = currentParts[reasoningIndex];
                    currentParts[reasoningIndex] = {
                      ...existing,
                      // Use .reasoning instead of .text
                      text: (existing.reasoning ?? existing.text ?? "") + token,
                    };
                  } else {
                    // Prepend reasoning block with the proper key
                    currentParts.unshift({
                      type: "reasoning",
                      text: token,
                    });
                  }

                  return {
                    ...msg,
                    content: currentParts,
                  };
                }),
              );
              return;
            }

            if (event === "token") {
              const assistantId = String(data.assistant_message_id);

              setMessages((prev) =>
                prev.map((msg) => {
                  if (msg.message_id !== assistantId) return msg;

                  const currentParts = Array.isArray(msg.content)
                    ? [...msg.content]
                    : [];
                  const textIndex = currentParts.findIndex(
                    (p) => p.type === "text",
                  );

                  if (textIndex !== -1) {
                    currentParts[textIndex] = {
                      ...currentParts[textIndex],
                      text: currentParts[textIndex].text + token,
                    };
                  } else {
                    currentParts.push({ type: "text", text: token });
                  }

                  return {
                    ...msg,
                    content: currentParts,
                  };
                }),
              );
              return;
            }

            if (event === "interrupt") {
              const assistantId = String(data.assistant_message_id);

              const interruptPayload = data.data as HumanReviewPayload;

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.message_id === assistantId
                    ? {
                        ...msg,
                        content: [
                          {
                            type: "text",
                            text: "This action requires your approval.",
                          },
                        ],
                        status: {
                          type: "requires-action",
                          reason: "interrupt",
                        },
                        hitl: interruptPayload,
                      }
                    : msg,
                ),
              );

              setIsRunning(false);

              return;
            }

            if (event === "sources") {
              const assistantId = String(data.assistant_message_id);

              const sources = Array.isArray(data.sources) ? data.sources : [];

              setMessages((prev) =>
                prev.map((msg) =>
                  msg.message_id === assistantId
                    ? {
                        ...msg,
                        ragSources: sources,
                      }
                    : msg,
                ),
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
          controller.signal,
        );
      } catch (error) {
        if (error instanceof DOMException && error.name === "AbortError") {
          console.log("Chat generation cancelled.");
          return;
        }

        console.error("Streaming error:", error);
      } finally {
        if (abortControllerRef.current === controller) {
          abortControllerRef.current = null;
        }

        setIsRunning(false);
      }
    },
    [conversationId],
  );

  const onCancel = useCallback(async () => {
    const controller = abortControllerRef.current;

    if (!controller) {
      return;
    }

    controller.abort();

    abortControllerRef.current = null;

    setIsRunning(false);
  }, []);

  const hasPendingHumanReview = messages.some(
    (message) => message.role === "assistant" && message.hitl != null,
  );

  const runtime = useExternalStoreRuntime({
    messages,
    convertMessage,
    isRunning,
    onNew,
    onCancel,
    isSendDisabled: hasPendingHumanReview,
  });

  return (
    <ChatContext.Provider
      value={{
        runtime,
        messages,
        isLoading,
        isRunning,
        conversationId,
        resumeHumanReview,
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
