module.exports = {
  apps: [
    {
      name: 'callified-ai',
      script: '/home/callified-ftp/callified_ai/start.sh',
      cwd: '/home/callified-ftp/callified_ai',
      interpreter: '/bin/bash',
      watch: false,
      autorestart: true,
      restart_delay: 5000,
      max_restarts: 10,
      min_uptime: '10s',
      log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
      error_file: '/home/callified-ftp/.pm2/logs/callified-ai-error.log',
      out_file: '/home/callified-ftp/.pm2/logs/callified-ai-out.log',
      merge_logs: true,
    },
  ],
};
