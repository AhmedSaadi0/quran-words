import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Allow LAN host for HMR/chunks when accessing dev server via 192.168.1.114
  // Covers both default port 3000 and fallback 3001 (Next matches origin string literally)
  allowedDevOrigins: [
    "192.168.1.114",
    "192.168.1.114:3000",
    "192.168.1.114:3001",
    "192.168.1.114:3002",
  ],
  images: {
    // No remote images in this app; skip sharp requirement
    unoptimized: true,
  },
};

export default nextConfig;
