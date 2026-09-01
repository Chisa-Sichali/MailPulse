/**
 * Pulls a human-readable message out of a FastAPI error response so the UI
 * can show the real reason instead of a generic "Failed to create user".
 *
 * FastAPI error bodies come in two shapes:
 *   - Business errors (e.g. 409 duplicate email): { "detail": "message" }
 *   - Validation errors (422): { "detail": [ { "msg": "..." }, ... ] }
 */
export async function extractErrorMessage(response: Response): Promise<string> {
  let message = '';

  try {
    const body = await response.json();

    if (typeof body.detail === 'string') {
      return body.detail;
    }

    if (Array.isArray(body.detail)) {
      return body.detail
        .map((entry: { msg?: string }) => entry.msg)
        .filter(Boolean)
        .join(', ');
    }

    switch (response.status) {
      case 409:
        return (message = 'Email already in use');

      case 422:
        return (message = 'Invalid email or password');

      case 401:
        return (message = 'Invalid email or password');

      default:
        return (message = 'Failed to create user');
    }
  } catch {}

  return `${message}`;
}

export function setTokens(accessToken: string, refreshToken: string) {
  try {
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
  } catch (error) {
    console.error('Error setting tokens:', error);
  }
}

export function removeTokens() {
  try {
    localStorage.removeItem('accessToken');
    localStorage.removeItem('refreshToken');
  } catch (error) {
    console.error('Error removing tokens:', error);
  }
}
