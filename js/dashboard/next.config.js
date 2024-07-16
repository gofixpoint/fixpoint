/** @type {import('next').NextConfig} */
const nextConfig = {
  webpack: (config, { defaultLoaders }) => {
    config.module.rules.push({
      test: /\.(jsx|tsx)$/,
      include: /\/uicomponents/,
      use: defaultLoaders.babel,
    });

    return config;
  },
};

module.exports = nextConfig;
