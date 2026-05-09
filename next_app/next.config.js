/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable Strict Mode in dev to avoid Leaflet double-initialization errors
  // This does NOT affect production builds.
  reactStrictMode: false,
  async headers() {
    return [
      {
        source: '/manifest.json',
        headers: [{ key: 'Content-Type', value: 'application/manifest+json' }],
      },
    ];
  },
}
module.exports = nextConfig
