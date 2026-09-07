import {
  AuthResponse,
  User,
  Issue,
  IssueDetail,
  Report,
  DuplicateCheckResponse,
  TaxonomyData,
  Notification,
  IssueStatus,
  EvidenceType,
  VerificationStatus,
  UserRole,
  IssueType,
  Location,
  RoutingRule,
  TimelineEvent,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";

class ApiClient {
  private getToken(): string | null {
    if (typeof window !== "undefined") {
      return localStorage.getItem("campuspulse_token");
    }
    return null;
  }

  public setToken(token: string) {
    if (typeof window !== "undefined") {
      localStorage.setItem("campuspulse_token", token);
    }
  }

  public clearToken() {
    if (typeof window !== "undefined") {
      localStorage.removeItem("campuspulse_token");
      localStorage.removeItem("campuspulse_user");
    }
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!response.ok) {
      let errorMsg = `HTTP Error ${response.status}`;
      try {
        const errorData = await response.json();
        if (errorData.detail) {
          errorMsg = typeof errorData.detail === "string" ? errorData.detail : JSON.stringify(errorData.detail);
        }
      } catch {
        // use default error message
      }
      throw new Error(errorMsg);
    }

    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Auth
  async login(email: string, password: string): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async register(data: {
    email: string;
    password: string;
    full_name: string;
    role?: UserRole;
    department?: string;
  }): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(data),
    });
    this.setToken(res.access_token);
    return res;
  }

  async demoLogin(role: UserRole): Promise<AuthResponse> {
    const res = await this.request<AuthResponse>("/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({ role }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<User> {
    return this.request<User>("/auth/me");
  }

  // Taxonomies
  async getTaxonomies(): Promise<TaxonomyData> {
    return this.request<TaxonomyData>("/admin/taxonomies");
  }

  // Reports
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
    return this.request<Report>("/reports", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getMyReports(): Promise<Report[]> {
    return this.request<Report[]>("/reports/my");
  }

  // Issues
  async getIssues(status?: IssueStatus): Promise<Issue[]> {
    const query = status ? `?status=${status}` : "";
    return this.request<Issue[]>(`/issues${query}`);
  }

  async getIssue(id: number): Promise<IssueDetail> {
    return this.request<IssueDetail>(`/issues/${id}`);
  }

  async getIssueHistory(id: number): Promise<TimelineEvent[]> {
    return this.request<TimelineEvent[]>(`/issues/${id}/history`);
  }

  async startProgress(id: number): Promise<IssueDetail> {
    return this.request<IssueDetail>(`/issues/${id}/progress`, {
      method: "POST",
    });
  }

  async resolveIssue(
    id: number,
    data: {
      evidence_type: EvidenceType;
      notes: string;
      attachment_url?: string;
    }
  ) {
    return this.request(`/issues/${id}/resolve`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async escalateIssue(
    id: number,
    data: {
      reason: string;
      escalated_to_id?: number;
    }
  ) {
    return this.request(`/issues/${id}/escalate`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async verifyIssue(
    id: number,
    data: {
      status: VerificationStatus;
      comment?: string;
    }
  ) {
    return this.request(`/issues/${id}/verify`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async reassignIssue(
    id: number,
    data: {
      handler_id: number;
      reason?: string;
    }
  ): Promise<IssueDetail> {
    return this.request<IssueDetail>(`/issues/${id}/reassign`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // Admin Config
  async listIssueTypes(): Promise<IssueType[]> {
    return this.request<IssueType[]>("/admin/issue-types");
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

  async listLocations(): Promise<Location[]> {
    return this.request<Location[]>("/admin/locations");
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
    return this.request<void>(`/admin/routing-rules/${id}`, {
      method: "DELETE",
    });
  }

  async listUsers(role?: UserRole): Promise<User[]> {
    const query = role ? `?role=${role}` : "";
    return this.request<User[]>(`/admin/users${query}`);
  }

  async triggerSeedData(): Promise<{ message: string }> {
    return this.request<{ message: string }>("/admin/seed-data", {
      method: "POST",
    });
  }

  // Notifications
  async getNotifications(): Promise<Notification[]> {
    return this.request<Notification[]>("/notifications");
  }

  async markNotificationRead(id: number): Promise<Notification> {
    return this.request<Notification>(`/notifications/${id}/read`, {
      method: "POST",
    });
  }

  async markAllNotificationsRead(): Promise<{ message: string }> {
    return this.request<{ message: string }>("/notifications/read-all", {
      method: "POST",
    });
  }
}

export const api = new ApiClient();

