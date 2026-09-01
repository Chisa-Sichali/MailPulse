import { CreateUserRequest, CreateUserResponse, LoginRequest } from './Types';
import { extractErrorMessage, setTokens } from '@/utils/auth-utils';
import { config } from '@/config/config';

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
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
    } catch (error) {
      console.error('Error creating user:', error);
      throw new Error('Could not reach the server. Please try again.');
    }

    if (!response.ok) {
      throw new Error(await extractErrorMessage(response));
    }

    const data = await response.json();
    setTokens(data.access_token, data.refresh_token);

    return data;
  }

  /**
   * Sends a request to the FastAPI backend to log in a user
   * @param request - The request body containing the user's email and password
   * @returns A promise that resolves to the response from the server
   */
  async LoginUser(request: LoginRequest): Promise<CreateUserResponse> {
    let response: Response;
    try {
      response = await fetch(`${this.baseUrl}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });
    } catch (error) {
      console.error('Error creating user:', error);
      throw new Error('Could not reach the server. Please try again.');
    }

    if (!response.ok) {
      throw new Error(await extractErrorMessage(response));
    }

    const data = await response.json();
    setTokens(data.access_token, data.refresh_token);

    return data;
  }
}

export const authService = new AuthService();
