import { useState } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { Textarea } from "@/components/ui/Textarea";
import { formatDateTime } from "@/lib/format";
import type { WorkCard } from "@/types/domain";

import { useAddComment } from "../hooks";

interface CommentModalProps {
  card: WorkCard | null;
  open: boolean;
  onClose: () => void;
}

export function CommentModal({ card, open, onClose }: CommentModalProps) {
  const [text, setText] = useState("");
  const addComment = useAddComment();

  if (!card) return null;

  const submit = () => {
    if (!text.trim()) return;
    addComment.mutate(
      { saleId: card.sale_id, text },
      { onSuccess: () => setText("") },
    );
  };

  return (
    <Modal
      open={open}
      title="Comentarios"
      onClose={onClose}
      footer={
        <>
          <Button variant="secondary" onClick={onClose}>
            Cerrar
          </Button>
          <Button onClick={submit} isLoading={addComment.isPending} disabled={!text.trim()}>
            Comentar
          </Button>
        </>
      }
    >
      <div className="flex flex-col gap-3">
        {card.comments.length === 0 && (
          <p className="text-sm text-slate-500">Todavía no hay comentarios.</p>
        )}
        {card.comments.map((comment) => (
          <div key={comment.id} className="rounded-lg bg-slate-50 px-3 py-2">
            <div className="flex items-center justify-between gap-2">
              <span className="text-sm font-medium text-slate-700">{comment.author_name}</span>
              <span className="text-xs text-slate-400">{formatDateTime(comment.created_at)}</span>
            </div>
            <p className="mt-1 text-sm text-slate-600">{comment.text}</p>
          </div>
        ))}
        {addComment.error && (
          <p className="text-xs text-red-600">{(addComment.error as Error).message}</p>
        )}
      </div>
      <div className="mt-4">
        <Textarea
          label="Nuevo comentario"
          name="comment"
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Escribí una nota…"
        />
      </div>
    </Modal>
  );
}
