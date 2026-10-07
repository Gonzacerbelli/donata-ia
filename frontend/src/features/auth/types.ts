export interface User {
  id: string;
  email: string | null;
  name: string | null;
  picture: string | null;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginPayload {
  username: string;
  password: string;
}