/** @type {import('next').NextConfig} */
const nextConfig = {
    // 允许跨域请求后端API
    async rewrites() {
        const apiUrl = process.env.API_URL || 'http://localhost:8000';
        return [
            {
                source: '/api/:path*',
                destination: `${apiUrl}/api/:path*`,
            },
        ];
    },
    // 图片域名白名单
    images: {
        remotePatterns: [
            {
                protocol: 'http',
                hostname: 'localhost',
            },
        ],
    },
};

module.exports = nextConfig;
