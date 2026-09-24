const backendUrl =
  process.env.INTERNAL_BACKEND_URL ||
  (process.env.NODE_ENV === "production" ? "http://backend:8000" : "http://localhost:8000");

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${backendUrl}/api/:path*`,
      },
    ];
  },
};

export default nextConfig;