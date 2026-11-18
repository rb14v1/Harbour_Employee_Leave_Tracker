import { ErrorAlert, EmptyState, Loading } from "../components/Feedback";
import { StatusBadge } from "../components/StatusBadge";
import { useResource } from "../hooks/useResource";
import { dashboardApi } from "../services/resources";
import { formatDate } from "../utils/format";

export function DashboardPage() {
  const { data, error, loading } = useResource(() => dashboardApi.get(), []);

  if (loading) return <Loading />;
  if (error || !data) return <ErrorAlert message={error ?? "No data returned."} />;

  const stats = [
    { label: "Total employees", value: data.employees.total, hint: `${data.employees.active} active` },
    { label: "Pending", value: data.leave_applications.pending },
    { label: "Approved", value: data.leave_applications.approved },
    { label: "Rejected", value: data.leave_applications.rejected },
    { label: "Cancelled", value: data.leave_applications.cancelled },
    { label: "On leave today", value: data.employees_on_leave.length, hint: formatDate(data.date) },
  ];

  return (
    <div className="page">
      <h1>Dashboard</h1>

      <section className="stat-grid">
        {stats.map((stat) => (
          <div className="card stat" key={stat.label}>
            <span className="muted">{stat.label}</span>
            <strong>{stat.value}</strong>
            {stat.hint && <span className="muted small">{stat.hint}</span>}
          </div>
        ))}
      </section>

      <section className="card">
        <h2>Employees on leave today</h2>
        {data.employees_on_leave.length === 0 ? (
          <EmptyState text="Nobody is on approved leave today." />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Leave type</th>
                <th>From</th>
                <th>To</th>
              </tr>
            </thead>
            <tbody>
              {data.employees_on_leave.map((row) => (
                <tr key={row.id}>
                  <td>
                    {row.employee_name} <span className="muted small">({row.employee_code})</span>
                  </td>
                  <td>{row.leave_type_name}</td>
                  <td>{formatDate(row.start_date)}</td>
                  <td>{formatDate(row.end_date)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>

      <section className="card">
        <h2>Applications by leave type</h2>
        <table>
          <thead>
            <tr>
              <th>Leave type</th>
              <th>Total</th>
              <th>Pending</th>
              <th>Approved</th>
              <th>Rejected</th>
              <th>Cancelled</th>
            </tr>
          </thead>
          <tbody>
            {data.by_leave_type.map((row) => (
              <tr key={row.id}>
                <td>{row.name}</td>
                <td>{row.total}</td>
                <td>{row.pending}</td>
                <td>{row.approved}</td>
                <td>{row.rejected}</td>
                <td>{row.cancelled}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card">
        <h2>Recent applications</h2>
        {data.recent_applications.length === 0 ? (
          <EmptyState text="No leave applications yet." />
        ) : (
          <table>
            <thead>
              <tr>
                <th>Employee</th>
                <th>Leave type</th>
                <th>Dates</th>
                <th>Days</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_applications.map((row) => (
                <tr key={row.id}>
                  <td>{row.employee_name}</td>
                  <td>{row.leave_type_name}</td>
                  <td>
                    {formatDate(row.start_date)} – {formatDate(row.end_date)}
                  </td>
                  <td>{row.number_of_days}</td>
                  <td>
                    <StatusBadge status={row.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </section>
    </div>
  );
}
