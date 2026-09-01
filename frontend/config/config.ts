export const config = {
  api_url: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:3000",
  fastapi_backend_url:
    process.env.NEXT_PUBLIC_FASTAPI_BACKEND_URL ?? "http://localhost:8000",
};
