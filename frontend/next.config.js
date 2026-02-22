const createNextIntlPlugin = require('next-intl/plugin');

const withNextIntl = createNextIntlPlugin();

/** @type {import('next').NextConfig} */
const nextConfig = {
  // output: 'export',
  images: {
    unoptimized: true,
  },
};

module.exports = withNextIntl(nextConfig);
