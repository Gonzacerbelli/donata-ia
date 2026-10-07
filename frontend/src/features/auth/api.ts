import { api } from "@/lib/http";

import type { LoginPayload, TokenResponse, User } from "./types";

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const { data } = await api.post<TokenResponse>("/auth/login", payload);
  return data;
}

export async function fetchMe(): Promise<User> {
  const { data } = await api.get<User>("/auth/me");
  return data;
}

export async function fetchGoogleLoginUrl(): Promise<string> {
  const { data } = await api.get<{ url: string }>("/auth/google");
  return data.url;
}