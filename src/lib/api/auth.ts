import { API_URL, resetSessionExpiredFlag } from "./client";

export interface User {
  id: string;
  name: string;
  email: string;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  user: User;
}

/**
 * Registers a new user, automatically establishing a cookie session.
 */
export async function registerUser(name: string, email: string, password: string): Promise<User> {
  const response = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name, email, password }),
    credentials: "include", // Essential for HttpOnly cookie exchange across ports
  });

  if (!response.ok) {
    let errorMsg = "Registration failed";
    try {
      const data = await response.json();
      if (data?.error?.message) {
        errorMsg = data.error.message;
      } else if (data?.detail) {
        errorMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }

  resetSessionExpiredFlag();
  const data: AuthResponse = await response.json();
  return data.user;
}

/**
 * Log in using credentials, storing access token in HttpOnly cookie.
 */
export async function loginUser(email: string, password: string): Promise<User> {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ email, password }),
    credentials: "include",
  });

  if (!response.ok) {
    let errorMsg = "Login failed";
    try {
      const data = await response.json();
      if (data?.error?.message) {
        errorMsg = data.error.message;
      } else if (data?.detail) {
        errorMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }

  resetSessionExpiredFlag();
  const data: AuthResponse = await response.json();
  return data.user;
}

/**
 * Log out and invalidate local HttpOnly token session.
 */
export async function logoutUser(): Promise<void> {
  const response = await fetch(`${API_URL}/api/auth/logout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    let errorMsg = "Logout request failed";
    try {
      const data = await response.json();
      if (data?.error?.message) {
        errorMsg = data.error.message;
      }
    } catch {
      // ignore
    }
    throw new Error(errorMsg);
  }
}

/**
 * Validates session and returns current user model.
 */
export async function getMe(): Promise<User> {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
    credentials: "include",
  });

  if (!response.ok) {
    throw new Error("Unauthorized session");
  }

  resetSessionExpiredFlag();
  const data: AuthResponse = await response.json();
  return data.user;
}
