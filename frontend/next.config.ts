import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a minimal Node runtime for the production image. This app uses
  // Server Actions and authenticated dynamic routes, so a static export would
  // silently remove required functionality.
  output: "standalone",
  // Allows a rolling deployment to tell an old client to reload rather than
  // mixing one release's HTML/Server Actions with another release's assets.
  deploymentId: process.env.DEPLOYMENT_VERSION,
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
        ],
      },
      {
        // Service worker must never be cached by the browser/CDN, or
        // updates to it stop reaching returning users.
        source: "/sw.js",
        headers: [
          {
            key: "Content-Type",
            value: "application/javascript; charset=utf-8",
          },
          {
            key: "Cache-Control",
            value: "no-cache, no-store, must-revalidate",
          },
          {
            key: "Content-Security-Policy",
            value: "default-src 'self'; script-src 'self'",
          },
        ],
      },
    ];
  },
};

export default nextConfig;
