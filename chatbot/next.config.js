/** @type {import('next').NextConfig} */
const ADMIN_APP_URL = process.env.NEXT_PUBLIC_ADMIN_URL || "http://localhost:3053";

const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:5052/api/v1",
    NEXT_PUBLIC_ADMIN_URL: ADMIN_APP_URL,
  },
  async redirects() {
    return [
      {
        source: "/admin",
        destination: `${ADMIN_APP_URL}/admin/login`,
        permanent: false,
      },
      {
        source: "/admin/:path*",
        destination: `${ADMIN_APP_URL}/admin/login`,
        permanent: false,
      },
    ];
  },
};

module.exports = nextConfig;
