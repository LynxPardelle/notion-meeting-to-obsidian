const backendPort = process.env.BACKEND_PORT || '8765';
const backendHost = process.env.BACKEND_HOST || '127.0.0.1';

module.exports = {
  '/api': {
    target: `http://${backendHost}:${backendPort}`,
    secure: false,
    changeOrigin: true,
    pathRewrite: {
      '^/api': ''
    }
  }
};
