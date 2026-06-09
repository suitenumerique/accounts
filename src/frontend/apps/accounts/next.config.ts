import path from "path";
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "export",
  reactStrictMode: false,
  // The monorepo lives in src/frontend; pin the tracing root so Next does not
  // pick an unrelated lockfile higher up the tree.
  outputFileTracingRoot: path.resolve(process.cwd(), "..", ".."),
};

export default nextConfig;
