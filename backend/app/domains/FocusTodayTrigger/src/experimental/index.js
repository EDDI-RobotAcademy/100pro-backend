/**
 * 실험군(Experimental) 전용 로직 진입점.
 * Session, Intervention, ExitAnalysis 서비스 및 API 라우트 노출.
 */
const routes = require('./routes');

module.exports = {
  routes,
  sessionService: require('./services/sessionService'),
  interventionService: require('./services/interventionService'),
  exitAnalysisService: require('./services/exitAnalysisService'),
  experimentGroup: require('./experimentGroup'),
};
