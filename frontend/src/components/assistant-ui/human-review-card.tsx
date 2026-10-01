import { CheckIcon, ShieldAlertIcon, XIcon } from "lucide-react";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { useChat } from "@/context/ChatContext";
import type { HumanReviewPayload } from "@/interfaces/chat";

interface HumanReviewCardProps {
  messageId: string;
  payload: HumanReviewPayload;
}

export function HumanReviewCard({ messageId, payload }: HumanReviewCardProps) {
  const { resumeHumanReview } = useChat();

  const [submitting, setSubmitting] = useState(false);

  const action = payload.action_requests?.[0];

  const toolName = action?.name ?? "Protected action";
  const args = action?.args ?? {};

  const orderId = String(args.order_id ?? "-");
  const amount = String(args.amount ?? "-");
  const reason = String(args.reason ?? "-");

  const handleDecision = async (decision: "approve" | "reject") => {
    if (submitting) {
      return;
    }

    setSubmitting(true);

    try {
      await resumeHumanReview(messageId, {
        decision,
        ...(decision === "reject"
          ? {
              message: "Refund rejected by user.",
            }
          : {}),
      });
    } catch (error) {
      console.error("Failed to submit human review:", error);
      setSubmitting(false);
    }
  };

  return (
    <div className="mt-4 rounded-xl border p-4">
      <div className="flex items-start gap-3">
        <ShieldAlertIcon className="mt-0.5 size-5" />

        <div className="flex-1">
          <div className="font-medium">Approval required</div>

          <div className="text-muted-foreground mt-1 text-sm">
            The assistant wants to execute <strong>{toolName}</strong>.
          </div>

          <div className="bg-muted mt-4 rounded-lg p-3 text-sm">
            <div>
              <strong>Order:</strong> {orderId}
            </div>

            <div>
              <strong>Amount:</strong> BRL {amount}
            </div>

            <div>
              <strong>Reason:</strong> {reason}
            </div>
          </div>

          <div className="mt-4 flex gap-2">
            <Button
              onClick={() => handleDecision("approve")}
              disabled={submitting}
            >
              <CheckIcon className="mr-2 size-4" />
              Approve
            </Button>

            <Button
              variant="outline"
              onClick={() => handleDecision("reject")}
              disabled={submitting}
            >
              <XIcon className="mr-2 size-4" />
              Reject
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
