export interface ChatStreamRequest {
  conversation_id?: string | null;
  message: string;
}

export interface StreamEvent {
  event: string;
  data: Record<string, unknown>;
}

const API_URL = "http://localhost:8000";

export async function streamChat(
  payload: ChatStreamRequest,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(`${API_URL}/messages/send-message`, {
    method: "POST",

    headers: {
      "Content-Type": "application/json",
    },

    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();

  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, {
      stream: true,
    });

    const events = buffer.split("\n\n");

    // Keep incomplete SSE event
    buffer = events.pop() || "";

    for (const rawEvent of events) {
      parseSSEEvent(rawEvent, onEvent);
    }
  }

  // Flush remaining decoder content
  buffer += decoder.decode();

  if (buffer.trim()) {
    parseSSEEvent(buffer, onEvent);
  }
}

function parseSSEEvent(
  rawEvent: string,
  onEvent: (event: StreamEvent) => void,
): void {
  const lines = rawEvent.split("\n");

  let eventName = "message";

  const dataLines: string[] = [];

  for (const line of lines) {
    if (line.startsWith("event:")) {
      eventName = line.slice("event:".length).trim();
    }

    if (line.startsWith("data:")) {
      dataLines.push(line.slice("data:".length).trim());
    }
  }

  if (dataLines.length === 0) {
    return;
  }

  const dataString = dataLines.join("\n");

  try {
    onEvent({
      event: eventName,
      data: JSON.parse(dataString),
    });
  } catch {
    console.error("Invalid SSE event:", rawEvent);
  }
}

export interface HumanReviewRequest {
  assistant_message_id: string;
  decision: "approve" | "reject";
  message?: string;
}

export async function resumeHumanReviewStream(
  conversationId: string,
  payload: HumanReviewRequest,
  onEvent: (event: StreamEvent) => void,
): Promise<void> {
  const response = await fetch(
    `${API_URL}/messages/conversations/${conversationId}/human-review`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    },
  );

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  if (!response.body) {
    throw new Error("Streaming is not supported by this browser.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();

    if (done) {
      break;
    }

    buffer += decoder.decode(value, {
      stream: true,
    });

    const events = buffer.split("\n\n");

    buffer = events.pop() || "";

    for (const rawEvent of events) {
      parseSSEEvent(rawEvent, onEvent);
    }
  }

  buffer += decoder.decode();

  if (buffer.trim()) {
    parseSSEEvent(buffer, onEvent);
  }
}
