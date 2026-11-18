import type {
  Dashboard,
  Employee,
  EmployeeInput,
  LeaveApplication,
  LeaveApplicationInput,
  LeaveBalance,
  LeaveType,
  LeaveTypeInput,
  Paginated,
} from "../types";
import { buildQuery, jsonBody, request } from "./api";

export interface ListParams {
  page?: number;
  search?: string;
  [key: string]: string | number | boolean | null | undefined;
}

export const employeeApi = {
  list: (params: ListParams) => request<Paginated<Employee>>(`/employees/${buildQuery(params)}`),
  listAll: () => request<Paginated<Employee>>(`/employees/${buildQuery({ page_size: 100 })}`),
  create: (data: EmployeeInput) => request<Employee>("/employees/", { method: "POST", body: jsonBody(data) }),
  update: (id: number, data: Partial<EmployeeInput>) =>
    request<Employee>(`/employees/${id}/`, { method: "PATCH", body: jsonBody(data) }),
  deactivate: (id: number) => request<void>(`/employees/${id}/`, { method: "DELETE" }),
};

export const leaveTypeApi = {
  list: () => request<Paginated<LeaveType>>(`/leave-types/${buildQuery({ page_size: 100 })}`),
  create: (data: LeaveTypeInput) => request<LeaveType>("/leave-types/", { method: "POST", body: jsonBody(data) }),
  update: (id: number, data: Partial<LeaveTypeInput>) =>
    request<LeaveType>(`/leave-types/${id}/`, { method: "PATCH", body: jsonBody(data) }),
  remove: (id: number) => request<void>(`/leave-types/${id}/`, { method: "DELETE" }),
};

export interface LeaveFilters extends ListParams {
  employee?: number | null;
  leave_type?: number | null;
  status?: string | null;
}

export const leaveApi = {
  list: (params: LeaveFilters) => request<Paginated<LeaveApplication>>(`/leaves/${buildQuery(params)}`),
  create: (data: LeaveApplicationInput) =>
    request<LeaveApplication>("/leaves/", { method: "POST", body: jsonBody(data) }),
  update: (id: number, data: Partial<LeaveApplicationInput>) =>
    request<LeaveApplication>(`/leaves/${id}/`, { method: "PATCH", body: jsonBody(data) }),
  remove: (id: number) => request<void>(`/leaves/${id}/`, { method: "DELETE" }),
  review: (id: number, action: "approve" | "reject" | "cancel", adminRemarks: string) =>
    request<LeaveApplication>(`/leaves/${id}/${action}/`, {
      method: "POST",
      body: jsonBody({ admin_remarks: adminRemarks }),
    }),
};

export const balanceApi = {
  list: (year: number, employee?: number | null) =>
    request<LeaveBalance[]>(`/leave-balances/${buildQuery({ year, employee })}`),
};

export const dashboardApi = {
  get: () => request<Dashboard>("/dashboard/"),
};
