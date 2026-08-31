import {
  AssistantRuntimeProvider,
  useExternalStoreRuntime,
  type AppendMessage,
  type ThreadMessageLike,
} from "@assistant-ui/react";

import {
  useCallback,
  useState,
  type ReactNode,
} from "react";

import { streamChat } from "@/api/chat";


type ChatRuntimeProviderProps = {

  conversationId:
    string | null;

  onConversationCreated:
    (
      conversationId: string,
    ) => void;

  children:
    ReactNode;

};


type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};


const convertMessage = (
  message: ChatMessage,
): ThreadMessageLike => {
  return {
    id: message.id,

    role: message.role,

    content: [
      {
        type: "text",
        text: message.content,
      },
    ],
  };
};


export function ChatRuntimeProvider({
  conversationId,
  onConversationCreated,
  children,
}: ChatRuntimeProviderProps) {


  const [messages, setMessages] =
    useState<ChatMessage[]>([]);

  const [isRunning, setIsRunning] =
    useState(false);


  const onNew = useCallback(
    async (message: AppendMessage) => {
      // --------------------------------
      // 1. Extract user text
      // --------------------------------

      const userText = message.content
        .filter(
          (part) => part.type === "text",
        )
        .map(
          (part) => part.text,
        )
        .join("");


      if (!userText.trim()) {
        return;
      }


      // --------------------------------
      // 2. Create temporary IDs
      // --------------------------------

      const temporaryUserId =
        crypto.randomUUID();

      const temporaryAssistantId =
        crypto.randomUUID();


      // --------------------------------
      // 3. Add messages locally
      // --------------------------------

      setMessages((previous) => [
        ...previous,

        {
          id: temporaryUserId,
          role: "user",
          content: userText,
        },

        {
          id: temporaryAssistantId,
          role: "assistant",
          content: "",
        },
      ]);


      setIsRunning(true);


      try {
        await streamChat(
          {
            conversation_id: conversationId,
            message: userText,
          },

          ({ event, data }) => {

            // ----------------------------
            // message_start
            // ----------------------------

            if (event === "message_start") {
              const backendConversationId =
                String(data.conversation_id);

              const backendUserId =
                String(data.user_message_id);

              const backendAssistantId =
                String(data.assistant_message_id);


              onConversationCreated(
                backendConversationId,
              );


              // Replace temporary IDs

              setMessages((previous) =>
                previous.map((current) => {
                  if (
                    current.id ===
                    temporaryUserId
                  ) {
                    return {
                      ...current,
                      id: backendUserId,
                    };
                  }


                  if (
                    current.id ===
                    temporaryAssistantId
                  ) {
                    return {
                      ...current,
                      id: backendAssistantId,
                    };
                  }


                  return current;
                }),
              );

              return;
            }


            // ----------------------------
            // token
            // ----------------------------

            if (event === "token") {
              const token =
                String(data.content ?? "");

              const assistantId =
                String(
                  data.assistant_message_id,
                );


              setMessages((previous) =>
                previous.map((current) => {
                  if (
                    current.id === assistantId
                  ) {
                    return {
                      ...current,

                      content:
                        current.content +
                        token,
                    };
                  }

                  return current;
                }),
              );

              return;
            }


            // ----------------------------
            // complete
            // ----------------------------

            if (event === "complete") {
              setIsRunning(false);
            }


            // ----------------------------
            // error
            // ----------------------------

            if (event === "error") {
              console.error(
                "Backend error:",
                data,
              );

              setIsRunning(false);
            }
          },
        );
      } catch (error) {
        console.error(
          "Streaming failed:",
          error,
        );
      } finally {
        setIsRunning(false);
      }
    },
    [conversationId],
  );


  // --------------------------------
  // assistant-ui runtime
  // --------------------------------

  const runtime =
    useExternalStoreRuntime({
      messages,

      convertMessage,

      isRunning,

      onNew,
    });


  return (
    <AssistantRuntimeProvider
      runtime={runtime}
    >
      {children}
    </AssistantRuntimeProvider>
  );
}