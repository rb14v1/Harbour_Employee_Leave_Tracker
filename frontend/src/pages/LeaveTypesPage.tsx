import { useState, type FormEvent } from "react";
import { EmptyState, ErrorAlert, Loading } from "../components/Feedback";
import { Modal } from "../components/Modal";
import { useResource } from "../hooks/useResource";
import { ApiError } from "../services/api";
import { leaveTypeApi } from "../services/resources";
import type { LeaveType, LeaveTypeInput } from "../types";

export function LeaveTypesPage() {
  const { data, error, loading, reload } = useResource(() => leaveTypeApi.list(), []);
  const [editing, setEditing] = useState<LeaveType | null>(null);
  const [creating, setCreating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  async function handleDelete(leaveType: LeaveType) {
    if (!window.confirm(`Delete "${leaveType.name}"? This is blocked if it is used by any application.`)) return;
    setActionError(null);
    try {
      await leaveTypeApi.remove(leaveType.id);
      reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not delete leave type.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Leave types</h1>
        <button type="button" className="button primary" onClick={() => setCreating(true)}>
          New leave type
        </button>
      </div>

      <ErrorAlert message={actionError ?? error} />

      {loading && !data ? (
        <Loading />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="No leave types defined." />
      ) : data ? (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Name</th>
                <th>Default annual allowance</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.results.map((leaveType) => (
                <tr key={leaveType.id}>
                  <td>{leaveType.name}</td>
                  <td>
                    {leaveType.default_annual_allowance === null
                      ? "Unlimited"
                      : `${leaveType.default_annual_allowance} days`}
                  </td>
                  <td className="actions">
                    <button type="button" className="button secondary small" onClick={() => setEditing(leaveType)}>
                      Edit
                    </button>
                    <button type="button" className="button danger small" onClick={() => handleDelete(leaveType)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {creating && (
        <LeaveTypeForm
          title="New leave type"
          initial={{ name: "", default_annual_allowance: 0 }}
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
          submit={(values) => leaveTypeApi.create(values)}
        />
      )}

      {editing && (
        <LeaveTypeForm
          title={`Edit ${editing.name}`}
          initial={{ name: editing.name, default_annual_allowance: editing.default_annual_allowance }}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            reload();
          }}
          submit={(values) => leaveTypeApi.update(editing.id, values)}
        />
      )}
    </div>
  );
}

interface LeaveTypeFormProps {
  title: string;
  initial: LeaveTypeInput;
  onClose: () => void;
  onSaved: () => void;
  submit: (values: LeaveTypeInput) => Promise<LeaveType>;
}

function LeaveTypeForm({ title, initial, onClose, onSaved, submit }: LeaveTypeFormProps) {
  const [name, setName] = useState(initial.name);
  const [unlimited, setUnlimited] = useState(initial.default_annual_allowance === null);
  const [allowance, setAllowance] = useState(String(initial.default_annual_allowance ?? 0));
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFieldErrors({});
    setFormError(null);
    setSaving(true);
    try {
      await submit({
        name: name.trim(),
        default_annual_allowance: unlimited ? null : Number(allowance),
      });
      onSaved();
    } catch (err) {
      if (err instanceof ApiError) {
        setFieldErrors(err.fieldErrors);
        setFormError(err.message);
      } else {
        setFormError("Could not save the leave type.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit}>
        <ErrorAlert message={formError} />
        <label className="field">
          <span>Name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} required />
          {fieldErrors.name && <span className="field-error">{fieldErrors.name}</span>}
        </label>
        <label className="field checkbox">
          <input type="checkbox" checked={unlimited} onChange={(e) => setUnlimited(e.target.checked)} />
          <span>Unlimited (no annual allowance)</span>
        </label>
        {!unlimited && (
          <label className="field">
            <span>Default annual allowance (days)</span>
            <input
              type="number"
              min={0}
              value={allowance}
              onChange={(e) => setAllowance(e.target.value)}
              required
            />
            {fieldErrors.default_annual_allowance && (
              <span className="field-error">{fieldErrors.default_annual_allowance}</span>
            )}
          </label>
        )}
        <div className="form-actions">
          <button type="button" className="button secondary" onClick={onClose}>
            Cancel
          </button>
          <button type="submit" className="button primary" disabled={saving}>
            {saving ? "Saving…" : "Save"}
          </button>
        </div>
      </form>
    </Modal>
  );
}
