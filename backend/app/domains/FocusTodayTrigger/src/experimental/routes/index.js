const express = require('express');
const sessionController = require('../controllers/sessionController');
const interventionController = require('../controllers/interventionController');

const router = express.Router();

// Session [PRO-B-30, PRO-B-32]
router.post('/session/app-open', sessionController.appOpen);
router.post('/session/action', sessionController.recordAction);
router.post('/session/app-close', sessionController.appClose);
router.get('/session/user/:user_id', sessionController.getSessions);
router.get('/session/user', sessionController.getSessions);

// Intervention [PRO-B-31]
router.get('/intervention/state', interventionController.getInterventionState);
router.post('/intervention/state', interventionController.getInterventionState);
router.post('/intervention/check', interventionController.checkInaction);

module.exports = router;
