import { useState, type FormEvent } from "react";
import { EmptyState, ErrorAlert, Loading } from "../components/Feedback";
import { Modal } from "../components/Modal";
import { Pagination } from "../components/Pagination";
import { useResource } from "../hooks/useResource";
import { ApiError } from "../services/api";
import { employeeApi } from "../services/resources";
import type { Employee, EmployeeInput } from "../types";
import { formatDate } from "../utils/format";

const PAGE_SIZE = 20;

const EMPTY_FORM: EmployeeInput = {
  employee_id: "",
  full_name: "",
  email: "",
  department: "",
  designation: "",
  joining_date: "",
  is_active: true,
};

export function EmployeesPage() {
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [page, setPage] = useState(1);
  const [editing, setEditing] = useState<Employee | null>(null);
  const [creating, setCreating] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);

  const { data, error, loading, reload } = useResource(
    () =>
      employeeApi.list({
        page,
        search: search.trim() || undefined,
        is_active: status === "" ? undefined : status === "active",
      }),
    [page, search, status],
  );

  async function handleDeactivate(employee: Employee) {
    if (!window.confirm(`Deactivate ${employee.full_name}? Their leave history is kept.`)) return;
    setActionError(null);
    try {
      await employeeApi.deactivate(employee.id);
      reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : "Could not deactivate employee.");
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Employees</h1>
        <button type="button" className="button primary" onClick={() => setCreating(true)}>
          New employee
        </button>
      </div>

      <div className="toolbar">
        <input
          placeholder="Search by ID, name, email, department"
          value={search}
          onChange={(e) => {
            setSearch(e.target.value);
            setPage(1);
          }}
        />
        <select
          value={status}
          onChange={(e) => {
            setStatus(e.target.value);
            setPage(1);
          }}
        >
          <option value="">All statuses</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>

      <ErrorAlert message={actionError ?? error} />

      {loading && !data ? (
        <Loading />
      ) : data && data.results.length === 0 ? (
        <EmptyState text="No employees match these filters." />
      ) : data ? (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee ID</th>
                <th>Name</th>
                <th>Email</th>
                <th>Department</th>
                <th>Designation</th>
                <th>Joined</th>
                <th>Status</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {data.results.map((employee) => (
                <tr key={employee.id}>
                  <td>{employee.employee_id}</td>
                  <td>{employee.full_name}</td>
                  <td>{employee.email}</td>
                  <td>{employee.department}</td>
                  <td>{employee.designation}</td>
                  <td>{formatDate(employee.joining_date)}</td>
                  <td>
                    <span className={`badge ${employee.is_active ? "badge-approved" : "badge-cancelled"}`}>
                      {employee.is_active ? "Active" : "Inactive"}
                    </span>
                  </td>
                  <td className="actions">
                    <button type="button" className="button secondary small" onClick={() => setEditing(employee)}>
                      Edit
                    </button>
                    {employee.is_active && (
                      <button
                        type="button"
                        className="button danger small"
                        onClick={() => handleDeactivate(employee)}
                      >
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          <Pagination page={page} count={data.count} pageSize={PAGE_SIZE} onChange={setPage} />
        </div>
      ) : null}

      {creating && (
        <EmployeeForm
          title="New employee"
          initial={EMPTY_FORM}
          onClose={() => setCreating(false)}
          onSaved={() => {
            setCreating(false);
            reload();
          }}
          submit={(values) => employeeApi.create(values)}
        />
      )}

      {editing && (
        <EmployeeForm
          title={`Edit ${editing.full_name}`}
          initial={{
            employee_id: editing.employee_id,
            full_name: editing.full_name,
            email: editing.email,
            department: editing.department,
            designation: editing.designation,
            joining_date: editing.joining_date,
            is_active: editing.is_active,
          }}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            reload();
          }}
          submit={(values) => employeeApi.update(editing.id, values)}
          showActiveToggle
        />
      )}
    </div>
  );
}

interface EmployeeFormProps {
  title: string;
  initial: EmployeeInput;
  onClose: () => void;
  onSaved: () => void;
  submit: (values: EmployeeInput) => Promise<Employee>;
  showActiveToggle?: boolean;
}

function EmployeeForm({ title, initial, onClose, onSaved, submit, showActiveToggle = false }: EmployeeFormProps) {
  const [values, setValues] = useState<EmployeeInput>(initial);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  function update<K extends keyof EmployeeInput>(key: K, value: EmployeeInput[K]) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
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
        setFormError("Could not save the employee.");
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
          <span>Employee ID</span>
          <input value={values.employee_id} onChange={(e) => update("employee_id", e.target.value)} required />
          {fieldError("employee_id")}
        </label>
        <label className="field">
          <span>Full name</span>
          <input value={values.full_name} onChange={(e) => update("full_name", e.target.value)} required />
          {fieldError("full_name")}
        </label>
        <label className="field">
          <span>Email</span>
          <input type="email" value={values.email} onChange={(e) => update("email", e.target.value)} required />
          {fieldError("email")}
        </label>
        <label className="field">
          <span>Department</span>
          <input value={values.department} onChange={(e) => update("department", e.target.value)} required />
          {fieldError("department")}
        </label>
        <label className="field">
          <span>Designation</span>
          <input value={values.designation} onChange={(e) => update("designation", e.target.value)} required />
          {fieldError("designation")}
        </label>
        <label className="field">
          <span>Joining date</span>
          <input type="date" value={values.joining_date} onChange={(e) => update("joining_date", e.target.value)} required />
          {fieldError("joining_date")}
        </label>
        {showActiveToggle && (
          <label className="field checkbox">
            <input
              type="checkbox"
              checked={values.is_active ?? true}
              onChange={(e) => update("is_active", e.target.checked)}
            />
            <span>Active</span>
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
