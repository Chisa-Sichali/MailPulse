import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // `standalone` emits `.next/standalone/server.js` plus a minimal
  // node_modules tree so the production Docker image can run without
  // shipping the full `node_modules` (and without running `npm install`
  // inside the runner stage). See frontend/Dockerfile.
  output: "standalone",
};

export default nextConfig;