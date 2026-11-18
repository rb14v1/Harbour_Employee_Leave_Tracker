interface PaginationProps {
  page: number;
  count: number;
  pageSize: number;
  onChange: (page: number) => void;
}

export function Pagination({ page, count, pageSize, onChange }: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(count / pageSize));
  return (
    <div className="pagination">
      <button type="button" className="button secondary" disabled={page <= 1} onClick={() => onChange(page - 1)}>
        Previous
      </button>
      <span className="muted">
        Page {page} of {totalPages} ({count} total)
      </span>
      <button
        type="button"
        className="button secondary"
        disabled={page >= totalPages}
        onClick={() => onChange(page + 1)}
      >
        Next
      </button>
    </div>
  );
}
