import type { ReactNode } from "react";
import { useAuth } from "../context/AuthContext";
import { ErrorAlert, Loading } from "./Feedback";

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) {
    return <Loading />;
  }
  if (!user) {
    return (
      <div className="login-page">
        <div className="card login-card">
          <ErrorAlert message="The app could not open. Set DEMO_AUTO_LOGIN=1 in backend/.env, restart the backend, then refresh this page." />
        </div>
      </div>
    );
  }
  return children;
}
