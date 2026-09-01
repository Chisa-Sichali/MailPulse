import { config } from '@/config/config';
import { authService } from '@/services/auth';
import { removeTokens } from '@/utils/auth-utils';

let refreshPromise: ReturnType<typeof authService.RefreshTokens> | null = null;

function getAccessToken() {
  return localStorage.getItem('accessToken');
}

function redirectToLogin() {
  if (typeof window !== 'undefined') {
    window.location.href = '/';
  }
}

async function refreshTokens() {
  refreshPromise ??= authService.RefreshTokens();

  try {
    return await refreshPromise;
  } finally {
    refreshPromise = null;
  }
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const request = (accessToken: string | null) => {
    const headers = new Headers(init.headers);
    headers.set('Content-Type', headers.get('Content-Type') ?? 'application/json');

    if (accessToken) {
      headers.set('Authorization', `Bearer ${accessToken}`);
    }

    return fetch(`${config.fastapi_backend_url}/api/v1${path}`, {
      ...init,
      headers,
    });
  };

  let response = await request(getAccessToken());

  if (response.status !== 401) {
    return response;
  }

  try {
    const tokens = await refreshTokens();
    response = await request(tokens.access_token);
    return response;
  } catch (error) {
    removeTokens();
    redirectToLogin();
    throw error;
  }
}
