import type { TextMessagePart, ThreadMessageLike } from "@assistant-ui/react";

export interface HumanReviewActionRequest {
  name: string;
  args: Record<string, unknown>;
  description?: string;
}

export interface HumanReviewConfig {
  action_name?: string;
  allowed_decisions?: string[];
  description?: string;
}

export interface HumanReviewPayload {
  action_requests: HumanReviewActionRequest[];
  review_configs: HumanReviewConfig[];
}

export interface BackendMessageStatus {
  type: string;
  reason?: string;
  interrupt?: HumanReviewPayload;
  human_review?: {
    decision: "approve" | "reject";
  };
}

export interface IConversation {
  conversation_id: string;
  title: string;
  is_pinned?: boolean;
  last_message_id?: string | null;
  updated_at?: string;
}

export interface IRawBackendMessage {
  message_id: string;
  conversation_id: string;
  parent_message_id?: string | null;
  role: "user" | "assistant" | "system";
  content: string | ThreadMessageLike["content"];
  status?: BackendMessageStatus | null;
  created_at?: string;
}

export interface IMessage extends ThreadMessageLike {
  conversation_id: string;
  message_id: string;
  parent_message_id?: string | null;

  hitl?: HumanReviewPayload;
}

export type { TextMessagePart };
