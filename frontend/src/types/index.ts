export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
}

export interface AuthConfig {
  demo_mode: boolean;
}

export interface Employee {
  id: number;
  employee_id: string;
  full_name: string;
  email: string;
  department: string;
  designation: string;
  joining_date: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EmployeeInput {
  employee_id: string;
  full_name: string;
  email: string;
  department: string;
  designation: string;
  joining_date: string;
  is_active?: boolean;
}

export interface LeaveType {
  id: number;
  name: string;
  default_annual_allowance: number | null;
  created_at: string;
  updated_at: string;
}

export interface LeaveTypeInput {
  name: string;
  default_annual_allowance: number | null;
}

export type LeaveStatus = "PENDING" | "APPROVED" | "REJECTED" | "CANCELLED";

export interface LeaveApplication {
  id: number;
  employee: number;
  employee_name: string;
  employee_code: string;
  leave_type: number;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  number_of_days: number;
  reason: string;
  applied_on: string;
  status: LeaveStatus;
  admin_remarks: string;
}

export interface LeaveApplicationInput {
  employee: number;
  leave_type: number;
  start_date: string;
  end_date: string;
  reason: string;
}

export interface LeaveBalance {
  employee_id: number;
  employee_code: string;
  employee_name: string;
  leave_type_id: number;
  leave_type_name: string;
  year: number;
  allocated: number | null;
  taken: number;
  remaining: number | null;
}

export interface DashboardRecentItem {
  id: number;
  employee_id: number;
  employee_code: string;
  employee_name: string;
  leave_type_name: string;
  start_date: string;
  end_date: string;
  number_of_days: number;
  status: LeaveStatus;
  applied_on: string;
}

export interface DashboardLeaveTypeRow {
  id: number;
  name: string;
  total: number;
  pending: number;
  approved: number;
  rejected: number;
  cancelled: number;
}

export interface Dashboard {
  date: string;
  employees: { total: number; active: number; inactive: number };
  leave_applications: {
    total: number;
    pending: number;
    approved: number;
    rejected: number;
    cancelled: number;
  };
  employees_on_leave: DashboardRecentItem[];
  by_leave_type: DashboardLeaveTypeRow[];
  recent_applications: DashboardRecentItem[];
}
