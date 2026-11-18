import { Route, Routes } from "react-router-dom";
import { Layout } from "./components/Layout";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { BalancesPage } from "./pages/BalancesPage";
import { DashboardPage } from "./pages/DashboardPage";
import { EmployeesPage } from "./pages/EmployeesPage";
import { LeaveApplicationsPage } from "./pages/LeaveApplicationsPage";
import { LeaveTypesPage } from "./pages/LeaveTypesPage";
import { NotFoundPage } from "./pages/NotFoundPage";

export default function App() {
  return (
    <Routes>
      <Route
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<DashboardPage />} />
        <Route path="employees" element={<EmployeesPage />} />
        <Route path="leave-types" element={<LeaveTypesPage />} />
        <Route path="leaves" element={<LeaveApplicationsPage />} />
        <Route path="balances" element={<BalancesPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
