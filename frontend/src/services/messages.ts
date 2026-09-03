import type { IMessage } from "@/interfaces";
import api from "@/lib/axios";

class Messages {
  getMessages = async (conversationId: string) => {
    return api
      .get(`/messages/get-messages/${conversationId}`)
      .then((response) => response.data);
  };
  sendMessage = async (message: IMessage) => {
    return api.post("/messages/send-message", message);
  };
}

const messagesService = new Messages();
export default messagesService;
