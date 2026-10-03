import { FileTextIcon } from "lucide-react";

import type { RagSource } from "@/interfaces";

interface RagSourceCardProps {
  sources: RagSource[];
}

function getSourceTitle(source: RagSource): string {
  if (source.document_id) {
    return source.document_id
      .replace(/[_-]+/g, " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  }

  const filename = source.source.split("/").pop();

  if (!filename) {
    return "Knowledge Base";
  }

  return filename
    .replace(/\.[^/.]+$/, "")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}

export function RagSourceCard({ sources }: RagSourceCardProps) {
  if (!sources.length) {
    return null;
  }

  return (
    <div className="mt-3 rounded-xl border bg-muted/30 p-3">
      <div className="mb-2 flex items-center gap-2 text-sm font-medium">
        <FileTextIcon className="size-4" />
        <span>Sources</span>
      </div>

      <div className="space-y-2">
        {sources.map((source, index) => (
          <div
            key={`${source.source}-${index}`}
            className="rounded-lg border bg-background px-3 py-2"
          >
            <div className="text-sm font-medium">{getSourceTitle(source)}</div>

            <div className="mt-0.5 text-xs text-muted-foreground">
              {source.source}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
