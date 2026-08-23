import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  images: {
    // No remote images in this app; skip sharp requirement
    unoptimized: true,
  },
};

export default nextConfig;
