/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable Strict Mode in dev to avoid Leaflet double-initialization errors
  // This does NOT affect production builds.
  reactStrictMode: false
}
module.exports = nextConfig
