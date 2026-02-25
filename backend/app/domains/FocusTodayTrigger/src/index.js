const express = require('express');
const config = require('./config');
const experimental = require('./experimental');
const { logger } = require('./logger');

const app = express();
app.use(express.json());

app.use('/experimental', experimental.routes);

app.get('/health', (req, res) => {
  res.json({ status: 'ok', task_display_scope: config.taskDisplayScope });
});

app.use((err, req, res, next) => {
  logger.error('request_error', { error: err.message, stack: err.stack });
  res.status(500).json({ error: 'Internal server error' });
});

app.listen(config.port, () => {
  logger.info(`Server listening on port ${config.port}`);
});
