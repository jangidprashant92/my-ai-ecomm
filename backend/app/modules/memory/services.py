import uuid

from app.ai.llm.base import BaseLLMProvider
from app.models.conversation import Message
from app.models.memory import ConversationSummaryMemory, UserMemory
from app.modules.messages.repository import MessagesRepository
from sqlmodel import Session, select


class UnifiedMemoryManager:
    """Manages unified memory operations for different memory types."""

    def __init__(
        self,
        session: Session,
        message_repo: MessagesRepository,
        llm: BaseLLMProvider,
    ):
        self.session = session
        self.message_repo = message_repo
        self.llm = llm

    # -------------------------------------------------------------
    # 1. BUFFER MEMORY (Sliding Window: last K messages)
    # -------------------------------------------------------------
    async def get_buffer_memory(
        self, conversation_id: uuid.UUID, limit: int = 6
    ) -> list[Message]:
        return await self.message_repo.get_last_messages(
            conversation_id=conversation_id, limit=limit
        )

    # -------------------------------------------------------------
    # 2. SUMMARY MEMORY (Rolling Conversation Compression)
    # -------------------------------------------------------------
    async def get_summary(self, conversation_id: uuid.UUID) -> str:
        record = self.session.get(ConversationSummaryMemory, conversation_id)
        return record.summary if record else ""

    async def update_summary_if_needed(
        self, conversation_id: uuid.UUID, threshold: int = 12
    ):
        # Count messages in this conversation
        statement = select(Message).where(Message.conversation_id == conversation_id)
        all_msgs = list(self.session.exec(statement).all())

        if len(all_msgs) < threshold:
            return

        # Fetch messages older than the last 6 buffer turns
        older_messages = all_msgs[:-6]
        if not older_messages:
            return

        existing_summary = await self.get_summary(conversation_id)

        history_text = "\n".join(
            [
                f"{m.role}: {m.content[0].get('text', '') if isinstance(m.content, list) else m.content}"
                for m in older_messages
            ]
        )

        compression_prompt = f"""
            Current Summary: {existing_summary}
            New messages to integrate:
            {history_text}

            Task: Update the summary of the conversation cleanly. Preserve key constraints, decisions, and goals. Keep it under 250 words.
            Updated Summary:
            """

        # Generate new condensed summary via LLM
        new_summary = await self.llm.generate(compression_prompt)

        record = self.session.get(ConversationSummaryMemory, conversation_id)
        if not record:
            record = ConversationSummaryMemory(
                conversation_id=conversation_id,
                summary=new_summary,
                last_summarized_message_id=older_messages[-1].message_id,
            )
            self.session.add(record)
        else:
            record.summary = new_summary
            record.last_summarized_message_id = older_messages[-1].message_id

        self.session.commit()

    # -------------------------------------------------------------
    # 3. VECTOR / RETRIEVAL MEMORY (Semantic Episodic Search)
    # -------------------------------------------------------------
    async def retrieve_relevant_context(
        self, conversation_id: uuid.UUID, query: str, top_k: int = 2
    ) -> list[str]:
        """
        Placeholder for vector similarity search.
        In production: embed `query` via embeddings API, run cosine similarity search
        against past messages or documents, and return matching excerpts.
        """
        # Example: return [] if vector index is empty or inactive
        return []

    # -------------------------------------------------------------
    # 4. USER PROFILE / ENTITY MEMORY (Facts & Preferences)
    # -------------------------------------------------------------
    async def get_user_profile_facts(self, user_id: uuid.UUID) -> list[str]:
        statement = select(UserMemory).where(UserMemory.user_id == user_id)
        records = self.session.exec(statement).all()
        return [f"- {r.key}: {r.value}" for r in records]

    async def extract_and_store_user_facts(self, user_id: uuid.UUID, user_text: str):
        """Asynchronously extract personal details/preferences mentioned in chat."""
        prompt = f"""
            Analyze this user message: "{user_text}"
            Does the user reveal explicit facts or preferences about themselves (e.g. name, tech stack, location, preferences)?
            Return JSON format: {{"found": true, "facts": [{{"key": "preferred_language", "value": "Python", "category": "preference"}}]}}
            If no facts are present, return {{"found": false, "facts": []}}
            """
        try:
            raw_response = await self.llm.generate(prompt)
            print(f"LLM response for user fact extraction: {raw_response}")
            # Parse result and insert into UserMemory if found is True
            # (Run as background task so it doesn't block the chat stream)

        except Exception:  # noqa: BLE001
            print(
                "Error extracting user facts from LLM response. Skipping user memory update."
            )
