const API_URL =
  "http://localhost:8000";


export interface Conversation {
  conversation_id: string;

  title: string | null;
}


export async function getConversations(): Promise<
  Conversation[]
> {
  const response = await fetch(
    `${API_URL}/conversations`,
  );


  if (!response.ok) {
    throw new Error(
      "Failed to load conversations",
    );
  }


  return response.json();
}