import {
  useState,
} from "react";

import {
  Thread,
} from "@/components/assistant-ui/elements/thread.aui";

import {
  ConversationSidebar,
} from "@/components/chat/ConversationSidebar";

import {
  ChatRuntimeProvider,
} from "@/components/chat/ChatRuntimeProvider";


export function ChatPage() {

  const [
    conversationId,
    setConversationId,
  ] = useState<string | null>(
    null,
  );


  function handleNewConversation() {

    setConversationId(
      null,
    );

  }


  function handleSelectConversation(
    id: string,
  ) {

    setConversationId(
      id,
    );

  }


  return (

    <div className="flex h-screen">

      {/* LEFT SIDEBAR */}

      <ConversationSidebar

        conversationId={
          conversationId
        }

        onSelectConversation={
          handleSelectConversation
        }

        onNewConversation={
          handleNewConversation
        }

      />


      {/* CHAT AREA */}

      <main className="min-w-0 flex-1">

        <ChatRuntimeProvider
          conversationId={
            conversationId
          }

          onConversationCreated={
            setConversationId
          }
        >

          <Thread />

        </ChatRuntimeProvider>

      </main>

    </div>

  );

}