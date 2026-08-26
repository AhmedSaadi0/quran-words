import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ["192.168.1.114", "192.168.1.114:3000"],
  images: {
    // No remote images in this app; skip sharp requirement
    unoptimized: true,
  },
};

export default nextConfig;
