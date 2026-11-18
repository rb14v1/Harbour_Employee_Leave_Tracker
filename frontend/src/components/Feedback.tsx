export function ErrorAlert({ message }: { message: string | null }) {
  if (!message) {
    return null;
  }
  return (
    <div className="alert alert-error" role="alert">
      {message}
    </div>
  );
}

export function Loading() {
  return <p className="muted">Loading…</p>;
}

export function EmptyState({ text }: { text: string }) {
  return <p className="muted empty">{text}</p>;
}
