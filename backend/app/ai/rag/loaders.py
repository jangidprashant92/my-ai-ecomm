from pathlib import Path

from langchain_core.documents import Document


class KnowledgeBaseLoader:
    """Loads Markdown knowledge-base documents."""

    def __init__(
        self,
        root_path: str,
    ) -> None:
        self.root_path = Path(root_path)

    def load(self) -> list[Document]:
        """Load all Markdown documents recursively."""

        if not self.root_path.exists():
            raise FileNotFoundError(
                f"Knowledge-base path does not exist: {self.root_path}"
            )

        documents: list[Document] = []

        for path in sorted(self.root_path.rglob("*.md")):
            if path.name.lower() == "readme.md":
                continue

            relative_path = path.relative_to(self.root_path)

            parts = relative_path.parts

            document_type = parts[0] if len(parts) > 1 else "general"

            category = path.stem

            documents.append(
                Document(
                    page_content=path.read_text(
                        encoding="utf-8",
                    ),
                    metadata={
                        "document_id": path.stem,
                        "source": str(relative_path),
                        "document_type": document_type,
                        "category": category,
                    },
                )
            )

        return documents
