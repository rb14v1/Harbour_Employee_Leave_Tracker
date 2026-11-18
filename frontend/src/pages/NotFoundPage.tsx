import { Link } from "react-router-dom";

export function NotFoundPage() {
  return (
    <div className="login-page">
      <div className="card login-card">
        <h1>Page not found</h1>
        <Link to="/">Back to dashboard</Link>
      </div>
    </div>
  );
}
