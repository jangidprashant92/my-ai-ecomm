import api from "@/lib/axios";

class Conversations {
  getConversations = async () => {
    return api.get("/conversations").then((response) => response.data);
  };
}

const conversationsService = new Conversations();
export default conversationsService;
