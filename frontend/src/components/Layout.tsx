import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/employees", label: "Employees" },
  { to: "/leave-types", label: "Leave types" },
  { to: "/leaves", label: "Leave applications" },
  { to: "/balances", label: "Balances" },
];

export function Layout() {
  const { user, logout, demoMode } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">Leave Tracker</div>
        <nav>
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.end} className="nav-link">
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>
      <div className="main">
        {demoMode && (
          <div className="demo-banner" role="status">
            Demo mode: signed in automatically as a demo administrator. Anyone with access to this app can change its data.
          </div>
        )}
        <header className="topbar">
          <span className="muted">Signed in as {user?.username}</span>
          {!demoMode && (
            <button type="button" className="button secondary" onClick={handleLogout}>
              Log out
            </button>
          )}
        </header>
        <main className="content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
