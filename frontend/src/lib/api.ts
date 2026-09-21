import {
  ApiErrorBody,
  AuthResponse,
  DuplicateCheckResponse,
  Escalation,
  Issue,
  IssueDetail,
  IssueScope,
  IssueStatus,
  IssueType,
  Location,
  Notification,
  Page,
  Report,
  ResolutionEvidence,
  RoutingPreview,
  RoutingRule,
  TaxonomyData,
  TimelineEvent,
  User,
  UserPublic,
  UserRole,
  Verification,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000/api/v1";
const TOKEN_KEY = "campuspulse_token";
const REQUEST_TIMEOUT_MS = 15000;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string;
  readonly fieldErrors: { field: string; message: string }[];

  constructor(
    status: number,
    code: string,
    message: string,
    requestId?: string,
    fieldErrors: { field: string; message: string }[] = []
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.requestId = requestId;
    this.fieldErrors = fieldErrors;
  }

  get isAuthError(): boolean {
    return this.status === 401;
  }

  get isNetworkError(): boolean {
    return this.status === 0;
  }
}

type SessionExpiredHandler = () => void;

class ApiClient {
  private onSessionExpired: SessionExpiredHandler | null = null;

  setSessionExpiredHandler(handler: SessionExpiredHandler | null) {
    this.onSessionExpired = handler;
  }

  getToken(): string | null {
    if (typeof window === "undefined") return null;
    return window.localStorage.getItem(TOKEN_KEY);
  }

  setToken(token: string) {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(TOKEN_KEY, token);
  }

  clearToken() {
    if (typeof window === "undefined") return;
    window.localStorage.removeItem(TOKEN_KEY);
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...((options.headers as Record<string, string>) ?? {}),
    };
    if (token) headers.Authorization = `Bearer ${token}`;

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    let response: Response;
    try {
      response = await fetch(`${API_BASE_URL}${endpoint}`, {
        ...options,
        headers,
        signal: controller.signal,
      });
    } catch (cause) {
      const timedOut = cause instanceof DOMException && cause.name === "AbortError";
      throw new ApiError(
        0,
        timedOut ? "timeout" : "network_error",
        timedOut
          ? "The server took too long to respond. Check your connection and try again."
          : "Could not reach the server. Check your connection and try again."
      );
    } finally {
      clearTimeout(timeout);
    }

    if (response.ok) {
      return response.status === 204 ? ({} as T) : ((await response.json()) as T);
    }

    let code = "http_error";
    let message = `Request failed (${response.status})`;
    let requestId: string | undefined;
    let fieldErrors: { field: string; message: string }[] = [];

    try {
      const body = (await response.json()) as ApiErrorBody;
      if (body?.error) {
        code = body.error.code ?? code;
        message = body.error.message ?? message;
        requestId = body.error.request_id;
        fieldErrors = body.error.details ?? [];
      }
    } catch {
      // A non-JSON error body means something upstream of the API failed; the status
      // code is all we have, and the generic message above already carries it.
    }

    if (response.status === 401) {
      this.clearToken();
      this.onSessionExpired?.();
    }

    throw new ApiError(response.status, code, message, requestId, fieldErrors);
  }

  private query(params: Record<string, string | number | boolean | undefined | null>): string {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== "") {
        search.set(key, String(value));
      }
    });
    const serialised = search.toString();
    return serialised ? `?${serialised}` : "";
  }

  async login(email: string, password: string): Promise<AuthResponse> {
    const result = await this.request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(result.access_token);
    return result;
  }

  async register(data: {
    email: string;
    password: string;
    full_name: string;
    department?: string;
    phone?: string;
  }): Promise<AuthResponse> {
    const result = await this.request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    this.setToken(result.access_token);
    return result;
  }

  async changePassword(currentPassword: string, newPassword: string): Promise<User> {
    return this.request<User>("/auth/change-password", {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
    });
  }

  async getMe(): Promise<User> {
    // Rejecting here rather than at the caller keeps "no token" and "bad token" on
    // the same asynchronous path, and saves a guaranteed-401 round trip.
    if (!this.getToken()) {
      throw new ApiError(401, "unauthenticated", "Not signed in");
    }
    return this.request<User>("/auth/me");
  }

  async getTaxonomies(): Promise<TaxonomyData> {
    return this.request<TaxonomyData>("/admin/taxonomies");
  }

  async checkDuplicate(data: {
    issue_type_id: number;
    location_id: number;
    specific_asset?: string;
  }): Promise<DuplicateCheckResponse> {
    return this.request<DuplicateCheckResponse>("/reports/check-duplicate", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async submitReport(data: {
    issue_type_id: number;
    location_id: number;
    description: string;
    specific_asset?: string;
    photo_url?: string;
    existing_issue_id?: number;
  }): Promise<Report> {
    return this.request<Report>("/reports", { method: "POST", body: JSON.stringify(data) });
  }

  async getMyReports(limit = 50, offset = 0): Promise<Page<Report>> {
    return this.request<Page<Report>>(`/reports/my${this.query({ limit, offset })}`);
  }

  async getIssues(params: {
    scope?: IssueScope;
    status?: IssueStatus;
    search?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<Page<Issue>> {
    return this.request<Page<Issue>>(`/issues${this.query(params)}`);
  }

  async getIssue(id: number): Promise<IssueDetail> {
    return this.request<IssueDetail>(`/issues/${id}`);
  }

  async getIssueHistory(id: number): Promise<TimelineEvent[]> {
    return this.request<TimelineEvent[]>(`/issues/${id}/history`);
  }

  async startProgress(id: number): Promise<IssueDetail> {
    return this.request<IssueDetail>(`/issues/${id}/progress`, { method: "POST" });
  }

  async resolveIssue(
    id: number,
    data: { evidence_type: string; notes: string; attachment_url?: string }
  ): Promise<ResolutionEvidence> {
    return this.request<ResolutionEvidence>(`/issues/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getEscalationTargets(id: number): Promise<UserPublic[]> {
    return this.request<UserPublic[]>(`/issues/${id}/escalation-targets`);
  }

  async escalateIssue(
    id: number,
    data: { reason: string; escalated_to_id?: number }
  ): Promise<Escalation> {
    return this.request<Escalation>(`/issues/${id}/escalate`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async verifyIssue(
    id: number,
    data: { status: string; comment?: string }
  ): Promise<Verification> {
    return this.request<Verification>(`/issues/${id}/verify`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async reassignIssue(id: number, data: { handler_id: number; reason?: string }): Promise<IssueDetail> {
    return this.request<IssueDetail>(`/issues/${id}/reassign`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listIssueTypes(includeInactive = false): Promise<IssueType[]> {
    return this.request<IssueType[]>(
      `/admin/issue-types${this.query({ include_inactive: includeInactive })}`
    );
  }

  async createIssueType(data: Partial<IssueType>): Promise<IssueType> {
    return this.request<IssueType>("/admin/issue-types", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateIssueType(id: number, data: Partial<IssueType>): Promise<IssueType> {
    return this.request<IssueType>(`/admin/issue-types/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async listLocations(includeInactive = false): Promise<Location[]> {
    return this.request<Location[]>(
      `/admin/locations${this.query({ include_inactive: includeInactive })}`
    );
  }

  async createLocation(data: Partial<Location>): Promise<Location> {
    return this.request<Location>("/admin/locations", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async listRoutingRules(): Promise<RoutingRule[]> {
    return this.request<RoutingRule[]>("/admin/routing-rules");
  }

  async createRoutingRule(data: {
    issue_type_id?: number | null;
    location_id?: number | null;
    handler_id: number;
    priority?: number;
  }): Promise<RoutingRule> {
    return this.request<RoutingRule>("/admin/routing-rules", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async deleteRoutingRule(id: number): Promise<void> {
    return this.request<void>(`/admin/routing-rules/${id}`, { method: "DELETE" });
  }

  async previewRouting(issueTypeId: number, locationId: number): Promise<RoutingPreview> {
    return this.request<RoutingPreview>("/admin/routing-rules/preview", {
      method: "POST",
      body: JSON.stringify({ issue_type_id: issueTypeId, location_id: locationId }),
    });
  }

  async listHandlers(): Promise<UserPublic[]> {
    return this.request<UserPublic[]>("/admin/handlers");
  }

  async listUsers(role?: UserRole, limit = 100, offset = 0): Promise<Page<User>> {
    return this.request<Page<User>>(`/admin/users${this.query({ role, limit, offset })}`);
  }

  async createStaffUser(data: {
    email: string;
    full_name: string;
    password: string;
    role: UserRole;
    department?: string;
  }): Promise<User> {
    return this.request<User>("/admin/users", { method: "POST", body: JSON.stringify(data) });
  }

  async getNotifications(limit = 30): Promise<Page<Notification>> {
    return this.request<Page<Notification>>(`/notifications${this.query({ limit })}`);
  }

  async getUnreadCount(): Promise<{ unread_count: number }> {
    return this.request<{ unread_count: number }>("/notifications/unread-count");
  }

  async markNotificationRead(id: number): Promise<Notification> {
    return this.request<Notification>(`/notifications/${id}/read`, { method: "POST" });
  }

  async markAllNotificationsRead(): Promise<{ marked_read: number }> {
    return this.request<{ marked_read: number }>("/notifications/read-all", { method: "POST" });
  }
}

export const api = new ApiClient();

export function errorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.fieldErrors.length > 0) {
      return error.fieldErrors.map((detail) => detail.message).join(". ");
    }
    return error.message;
  }
  if (error instanceof Error) return error.message;
  return "Something went wrong. Please try again.";
}
