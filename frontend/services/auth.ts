import { CreateUserRequest, CreateUserResponse, LoginRequest } from "./Types";
import { config } from "@/config/config";

class AuthService {
  private baseUrl = config.fastapi_backend_url;

  /**
     * Sends a request to the FastAPI backend to create a new User
     * @param request - The request body containing the user's email, password and username
     * @returns A promise that resolves to the response from the server
     '
     * */
  async CreateUser(request: CreateUserRequest): Promise<CreateUserResponse> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}/api/v1/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });
    } catch (error) {
      console.error("Error creating user:", error);
      throw new Error("Could not reach the server. Please try again.");
    }

    if (!response.ok) {
      throw new Error(await this.extractErrorMessage(response));
    }

    return response.json();
  }

  /**
   * Sends a request to the FastAPI backend to log in a user
   * @param request - The request body containing the user's email and password
   * @returns A promise that resolves to the response from the server
   */
  async LoginUser(request: LoginRequest): Promise<CreateUserResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(await this.extractErrorMessage(response));
      }

      return response.json();
    } catch (error) {
      console.error("Error creating user:", error);
      throw new Error("Could not reach the server. Please try again.");
    }
  }

  /**
   * Pulls a human-readable message out of a FastAPI error response so the UI
   * can show the real reason instead of a generic "Failed to create user".
   *
   * FastAPI error bodies come in two shapes:
   *   - Business errors (e.g. 409 duplicate email): { "detail": "message" }
   *   - Validation errors (422): { "detail": [ { "msg": "..." }, ... ] }
   */
  private async extractErrorMessage(response: Response): Promise<string> {
    let message = "";

    try {
      const body = await response.json();

      if (typeof body.detail === "string") {
        return body.detail;
      }

      if (Array.isArray(body.detail)) {
        return body.detail
          .map((entry: { msg?: string }) => entry.msg)
          .filter(Boolean)
          .join(", ");
      }

      switch (response.status) {
        case 409:
          return (message = "Email already in use");

        case 422:
          return (message = "Invalid email or password");

        default:
          return (message = "Failed to create user");
      }
    } catch {}

    return `${message}`;
  }
}

export const authService = new AuthService();
