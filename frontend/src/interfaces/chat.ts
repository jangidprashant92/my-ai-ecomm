import type {
  MessageStatus,
  TextMessagePart,
  ThreadMessageLike,
} from "@assistant-ui/react";

export interface IConversation {
  conversation_id: string;
  title: string;
  is_pinned?: boolean;
  last_message_id?: string | null;
  updated_at?: string;
}

// Shape received from FastAPI
export interface IRawBackendMessage {
  message_id: string;
  conversation_id: string;
  parent_message_id?: string | null;
  role: "user" | "assistant" | "system";
  content: string | ThreadMessageLike["content"];
  status?: MessageStatus | null;
  created_at?: string;
}

export interface IMessage extends ThreadMessageLike {
  conversation_id: string;
  message_id: string;
  parent_message_id?: string | null;
}

export type { TextMessagePart };
