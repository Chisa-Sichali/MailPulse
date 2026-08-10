export interface CreateUserRequest {
  email: string;
  password: string;
  username: string;
}

export interface CreateUserResponse {
  accessToken: string;
  refreshToken: string;
  token_type: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}
