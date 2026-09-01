export interface CreateUserRequest {
  email: string;
  password: string;
  username: string;
}

export interface CreateUserResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
