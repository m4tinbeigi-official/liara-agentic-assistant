import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: 'export',
  // Disable image optimization as it's not supported in static exports by default
  images: {
    unoptimized: true,
  },
  // Ensure that API calls point to the same origin in production
  env: {
    NEXT_PUBLIC_API_URL: process.env.NODE_ENV === 'development' ? 'http://localhost:8000' : '',
  }
};

export default nextConfig;
