import { useState, type FormEvent } from "react";
import { EmptyState, ErrorAlert, Loading } from "../components/Feedback";
import { Modal } from "../components/Modal";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { ApiError } from "../services/api";
import { employeeApi, leaveApi, leaveTypeApi } from "../services/resources";
import type { LeaveApplication, LeaveApplicationInput, LeaveStatus } from "../types";
import { formatDate } from "../utils/format";

const PAGE_SIZE = 20;
const STATUSES: LeaveStatus[] = ["PENDING", "APPROVED", "REJECTED", "CANCELLED"];

type ReviewAction = "approve" | "reject" | "cancel";

const REVIEW_LABELS: Record<ReviewAction, string> = {
  approve: "Approve",
  reject: "Reject",
  cancel: "Cancel application",
};

export function LeaveApplicationsPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [employeeFilter, setEmployeeFilter] = useState("");
  const [leaveTypeFilter, setLeaveTypeFilter] = useState("");
  const [page, setPage] = useState(1);
  const [creating, setCreating] = useState(false);
  const [editing, setEditing] = useState<LeaveApplication | null>(null);
  const [reviewing, setReviewing] = useState<{ application: LeaveApplication; action: ReviewAction } | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, error, loading, reload } = useResource(
    () =>
      leaveApi.list({
        page,
        search: search.trim() || undefined,
        status: status || undefined,
        employee: employeeFilter ? Number(employeeFilter) : undefined,
        leave_type: leaveTypeFilter ? Number(leaveTypeFilter) : undefined,
      }),
    [page, search, status, employeeFilter, leaveTypeFilter],
  );
  const employees = useResource(() => employeeApi.listAll(), []);
  const leaveTypes = useResource(() => leaveTypeApi.list(), []);

  function changePage(next: number) {
    setPage(next);
  }

  function resetPageOn<T>(setter: (value: T) => void) {
    return (value: T) => {
      setter(value);
      setPage(1);
    };
  }

  async function handleDelete(application: LeaveApplication) {
    if (!window.confirm("Delete this leave application?")) return;
    setActionError(null);
    try {
      await leaveApi.remove(application.id);
      reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not delete the application.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Leave applications</h1>
        <button type="button" className="button primary" onClick={() => setCreating(true)}>
          New application
        </button>
      </div>

      <div className="toolbar">
        <input
          placeholder="Search reason or employee"
          value={search}
          onChange={(e) => resetPageOn(setSearch)(e.target.value)}
        />
        <select value={status} onChange={(e) => resetPageOn(setStatus)(e.target.value)}>
          <option value="">All statuses</option>
          {STATUSES.map((value) => (
            <option key={value} value={value}>
              {value.charAt(0) + value.slice(1).toLowerCase()}
            </option>
          ))}
        </select>
        <select value={employeeFilter} onChange={(e) => resetPageOn(setEmployeeFilter)(e.target.value)}>
          <option value="">All employees</option>
          {employees.data?.results.map((employee) => (
            <option key={employee.id} value={employee.id}>
              {employee.full_name}
            </option>
          ))}
        </select>
        <select value={leaveTypeFilter} onChange={(e) => resetPageOn(setLeaveTypeFilter)(e.target.value)}>
          <option value="">All leave types</option>
          {leaveTypes.data?.results.map((leaveType) => (
            <option key={leaveType.id} value={leaveType.id}>
              {leaveType.name}
            </option>
          ))}
        </select>
      </div>

      <ErrorAlert message={actionError ?? error} />

      {loading && !data ? (
        <Loading />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="No leave applications match these filters." />
      ) : data ? (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Leave type</th>
                <th>Dates</th>
                <th>Days</th>
                <th>Reason</th>
                <th>Status</th>
                <th>Remarks</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.results.map((application) => (
                <tr key={application.id}>
                  <td>
                    {application.employee_name}
                    <div className="muted small">{application.employee_code}</div>
                  </td>
                  <td>{application.leave_type_name}</td>
                  <td>
                    {formatDate(application.start_date)} – {formatDate(application.end_date)}
                  </td>
                  <td>{application.number_of_days}</td>
                  <td className="wrap">{application.reason}</td>
                  <td>
                    <StatusBadge status={application.status} />
                  </td>
                  <td className="wrap muted small">{application.admin_remarks || "—"}</td>
                  <td className="actions">
                    {application.status === "PENDING" && (
                      <>
                        <button
                          type="button"
                          className="button primary small"
                          onClick={() => setReviewing({ application, action: "approve" })}
                        >
                          Approve
                        </button>
                        <button
                          type="button"
                          className="button danger small"
                          onClick={() => setReviewing({ application, action: "reject" })}
                        >
                          Reject
                        </button>
                        <button type="button" className="button secondary small" onClick={() => setEditing(application)}>
                          Edit
                        </button>
                      </>
                    )}
                    {application.status === "APPROVED" && (
                      <button
                        type="button"
                        className="button secondary small"
                        onClick={() => setReviewing({ application, action: "cancel" })}
                      >
                        Cancel
                      </button>
                    )}
                    {application.status !== "APPROVED" && (
                      <button type="button" className="button danger small" onClick={() => handleDelete(application)}>
                        Delete
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={changePage} />
        </div>
      ) : null}

      {creating && (
        <ApplicationForm
          title="New leave application"
          initial={{ employee: 0, leave_type: 0, start_date: "", end_date: "", reason: "" }}
          employees={employees.data?.results ?? []}
          leaveTypes={leaveTypes.data?.results ?? []}
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
          submit={(values) => leaveApi.create(values)}
        />
      )}

      {editing && (
        <ApplicationForm
          title="Edit leave application"
          initial={{
            employee: editing.employee,
            leave_type: editing.leave_type,
            start_date: editing.start_date,
            end_date: editing.end_date,
            reason: editing.reason,
          }}
          employees={employees.data?.results ?? []}
          leaveTypes={leaveTypes.data?.results ?? []}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            reload();
          }}
          submit={(values) => leaveApi.update(editing.id, values)}
        />
      )}

      {reviewing && (
        <ReviewModal
          application={reviewing.application}
          action={reviewing.action}
          onClose={() => setReviewing(null)}
          onDone={() => {
            setReviewing(null);
            reload();
          }}
        />
      )}
    </div>
  );
}

interface ApplicationFormProps {
  title: string;
  initial: LeaveApplicationInput;
  employees: { id: number; full_name: string; employee_id: string; is_active: boolean }[];
  leaveTypes: { id: number; name: string }[];
  onClose: () => void;
  onSaved: () => void;
  submit: (values: LeaveApplicationInput) => Promise<LeaveApplication>;
}

function ApplicationForm({ title, initial, employees, leaveTypes, onClose, onSaved, submit }: ApplicationFormProps) {
  const [values, setValues] = useState<LeaveApplicationInput>(initial);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function update<K extends keyof LeaveApplicationInput>(key: K, value: LeaveApplicationInput[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!values.employee || !values.leave_type) {
      setFormError("Choose an employee and a leave type.");
      return;
    }
    setFieldErrors({});
    setFormError(null);
    setSaving(true);
    try {
      await submit(values);
      onSaved();
    } catch (err) {
      if (err instanceof ApiError) {
        setFieldErrors(err.fieldErrors);
        setFormError(err.message);
      } else {
        setFormError("Could not save the application.");
      }
    } finally {
      setSaving(false);
    }
  }

  const fieldError = (name: string) => (fieldErrors[name] ? <span className="field-error">{fieldErrors[name]}</span> : null);

  return (
    <Modal title={title} onClose={onClose}>
      <form className="form-grid" onSubmit={handleSubmit}>
        <ErrorAlert message={formError} />
        <label className="field">
          <span>Employee</span>
          <select value={values.employee || ""} onChange={(e) => update("employee", Number(e.target.value))} required>
            <option value="">Select an employee</option>
            {employees.map((employee) => (
              <option key={employee.id} value={employee.id} disabled={!employee.is_active}>
                {employee.full_name} ({employee.employee_id}){employee.is_active ? "" : " – inactive"}
              </option>
            ))}
          </select>
          {fieldError("employee")}
        </label>
        <label className="field">
          <span>Leave type</span>
          <select
            value={values.leave_type || ""}
            onChange={(e) => update("leave_type", Number(e.target.value))}
            required
          >
            <option value="">Select a leave type</option>
            {leaveTypes.map((leaveType) => (
              <option key={leaveType.id} value={leaveType.id}>
                {leaveType.name}
              </option>
            ))}
          </select>
          {fieldError("leave_type")}
        </label>
        <label className="field">
          <span>Start date</span>
          <input type="date" value={values.start_date} onChange={(e) => update("start_date", e.target.value)} required />
          {fieldError("start_date")}
        </label>
        <label className="field">
          <span>End date</span>
          <input type="date" value={values.end_date} onChange={(e) => update("end_date", e.target.value)} required />
          {fieldError("end_date")}
        </label>
        <label className="field full">
          <span>Reason</span>
          <textarea value={values.reason} onChange={(e) => update("reason", e.target.value)} rows={3} required />
          {fieldError("reason")}
        </label>
        <div className="form-actions full">
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

interface ReviewModalProps {
  application: LeaveApplication;
  action: ReviewAction;
  onClose: () => void;
  onDone: () => void;
}

function ReviewModal({ application, action, onClose, onDone }: ReviewModalProps) {
  const [remarks, setRemarks] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  async function handleConfirm() {
    setError(null);
    setSaving(true);
    try {
      await leaveApi.review(application.id, action, remarks.trim());
      onDone();
    } catch (err) {
      setError(err instanceof Error ? err.message : "The action could not be completed.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <Modal title={`${REVIEW_LABELS[action]}: ${application.employee_name}`} onClose={onClose}>
      <div className="form-grid">
        <ErrorAlert message={error} />
        <p className="muted">
          {application.leave_type_name}, {formatDate(application.start_date)} – {formatDate(application.end_date)} (
          {application.number_of_days} day{application.number_of_days === 1 ? "" : "s"})
        </p>
        <label className="field full">
          <span>Admin remarks (optional)</span>
          <textarea value={remarks} onChange={(e) => setRemarks(e.target.value)} rows={3} maxLength={1000} />
        </label>
        <div className="form-actions full">
          <button type="button" className="button secondary" onClick={onClose}>
            Back
          </button>
          <button
            type="button"
            className={action === "approve" ? "button primary" : "button danger"}
            onClick={handleConfirm}
            disabled={saving}
          >
            {saving ? "Working…" : REVIEW_LABELS[action]}
          </button>
        </div>
      </div>
    </Modal>
  );
}
