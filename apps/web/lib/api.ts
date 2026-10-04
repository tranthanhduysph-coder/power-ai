import { auth } from "./firebase";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
const AUTH_MODE = process.env.NEXT_PUBLIC_AUTH_MODE || "firebase";

export class PowerApiError extends Error {
  status?: number;
  code?: string;

  constructor(message: string, options: { status?: number; code?: string } = {}) {
    super(message);
    this.name = "PowerApiError";
    this.status = options.status;
    this.code = options.code;
  }
}

function authErrorMessage(error: unknown): PowerApiError {
  const candidate = error as { code?: string; message?: string } | null;
  const code = candidate?.code || "auth/token-failed";
  if (code.includes("network-request-failed")) {
    return new PowerApiError(
      "Không thể kết nối Firebase Auth. Hãy kiểm tra Auth Emulator ở 127.0.0.1:9099 rồi thử lại.",
      { code: "auth_unavailable" }
    );
  }
  if (code.includes("user-token-expired") || code.includes("id-token-expired")) {
    return new PowerApiError("Phiên đăng nhập đã hết hạn. Hãy đăng nhập lại.", { code: "auth_expired" });
  }
  return new PowerApiError(candidate?.message || "Không thể lấy mã xác thực Firebase.", { code });
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers || {});
  headers.set("Content-Type", "application/json");

  if (AUTH_MODE === "dev") {
    headers.set("X-Dev-User", "local-demo-student");
  } else {
    const user = auth.currentUser;
    if (!user) throw new PowerApiError("Bạn chưa đăng nhập.", { code: "not_authenticated" });
    try {
      const token = await user.getIdToken();
      headers.set("Authorization", `Bearer ${token}`);
    } catch (error) {
      throw authErrorMessage(error);
    }
  }

  let response: Response;
  try {
    response = await fetch(`${API_URL}${path}`, {
      ...init,
      headers,
      cache: init.cache ?? "no-store",
    });
  } catch (error) {
    throw new PowerApiError(
      "Không thể kết nối POWER API ở localhost:8000. Hãy kiểm tra FastAPI rồi thử lại.",
      { code: "api_unavailable" }
    );
  }

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const detail = body?.detail;
    const message = typeof detail === "string"
      ? detail
      : detail?.reason || detail?.status || `API error ${response.status}`;
    throw new PowerApiError(message, { status: response.status, code: "api_error" });
  }
  return response.json() as Promise<T>;
}

export const apiBaseUrl = API_URL;
