const crypto = require('crypto');

const buildId = crypto.randomBytes(256).toString('hex').slice(0, 8);

/** @type {import('next').NextConfig} */
const nextConfig = {
  allowedDevOrigins: ['accounts.127.0.0.1.nip.io'],
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
  compiler: {
    // Enables the styled-components SWC transform
    styledComponents: true,
  },
  experimental: {
    // Tree-shake barrel files for these packages so webpack only bundles the
    // symbols that are actually imported, reducing chunk sizes noticeably for
    // Mantine and the Cunningham design system.
    optimizePackageImports: ['@mantine/core', '@mantine/hooks', 'lodash'],
  },
  generateBuildId: () => buildId,
  env: {
    NEXT_PUBLIC_BUILD_ID: buildId,
  },
  /**
   * In dev mode, Next.js doesn't use Webpack, but Turbopack.
   */
  turbopack: {
    rules: {
      '*.svg': {
        loaders: ['@svgr/webpack'],
        as: '*.js',
      },
    },
  },
  webpack(config) {
    // Grab the existing rule that handles SVG imports
    const fileLoaderRule = config.module.rules.find((rule) =>
      rule.test?.test?.('.svg'),
    );

    config.module.rules.push(
      // Reapply the existing rule, but only for svg imports ending in ?url
      {
        ...fileLoaderRule,
        test: /\.svg$/i,
        resourceQuery: /url/, // *.svg?url
      },
      // Convert all other *.svg imports to React components
      {
        test: /\.svg$/i,
        issuer: fileLoaderRule.issuer,
        resourceQuery: { not: [...fileLoaderRule.resourceQuery.not, /url/] }, // exclude if *.svg?url
        use: ['@svgr/webpack'],
      },
    );

    // Modify the file loader rule to ignore *.svg, since we have it handled now.
    fileLoaderRule.exclude = /\.svg$/i;

    return config;
  },
};

module.exports = nextConfig;
