import { useState } from "react";
import { EmptyState, ErrorAlert, Loading } from "../components/Feedback";
import { useResource } from "../hooks/useResource";
import { balanceApi, employeeApi } from "../services/resources";

export function BalancesPage() {
  const currentYear = new Date().getFullYear();
  const [year, setYear] = useState(currentYear);
  const [employeeFilter, setEmployeeFilter] = useState("");

  const employees = useResource(() => employeeApi.listAll(), []);
  const { data, error, loading } = useResource(
    () => balanceApi.list(year, employeeFilter ? Number(employeeFilter) : null),
    [year, employeeFilter],
  );

  return (
    <div className="page">
      <div className="page-header">
        <h1>Leave balances</h1>
      </div>

      <div className="toolbar">
        <label className="field inline">
          <span>Year</span>
          <input
            type="number"
            value={year}
            min={2000}
            max={2100}
            onChange={(e) => setYear(Number(e.target.value) || currentYear)}
          />
        </label>
        <select value={employeeFilter} onChange={(e) => setEmployeeFilter(e.target.value)}>
          <option value="">All employees</option>
          {employees.data?.results.map((employee) => (
            <option key={employee.id} value={employee.id}>
              {employee.full_name} ({employee.employee_id})
            </option>
          ))}
        </select>
      </div>

      <p className="muted small">
        Balances count approved leave only, grouped by the calendar year the leave starts in. Pending and rejected
        applications are not deducted.
      </p>

      <ErrorAlert message={error} />

      {loading && !data ? (
        <Loading />
      ) : data && data.length === 0 ? (
        <EmptyState text="No balances to show." />
      ) : data ? (
        <div className="card table-wrap">
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Leave type</th>
                <th>Allocated</th>
                <th>Taken</th>
                <th>Remaining</th>
              </tr>
            </thead>
            <tbody>
              {data.map((row) => (
                <tr key={`${row.employee_id}-${row.leave_type_id}`}>
                  <td>
                    {row.employee_name}
                    <div className="muted small">{row.employee_code}</div>
                  </td>
                  <td>{row.leave_type_name}</td>
                  <td>{row.allocated === null ? "Unlimited" : `${row.allocated} days`}</td>
                  <td>{row.taken} days</td>
                  <td className={row.remaining !== null && row.remaining <= 0 ? "text-danger" : undefined}>
                    {row.remaining === null ? "Unlimited" : `${row.remaining} days`}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
