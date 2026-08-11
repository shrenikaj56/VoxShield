import unittest
from modules.risk_engine import run_risk_engine
from modules.context_analysis import calculate_context_risk


class VoxShieldRiskEngineTests(unittest.TestCase):
    def test_context_risk_is_calculated(self):
        result = calculate_context_risk({
            'suspicious_call': True,
            'screen_sharing': True,
            'remote_control': False,
            'unknown_caller': True,
        })
        self.assertEqual(result['score'], 58)
        self.assertIn('Suspicious active call', result['reasons'])
        self.assertIn('Screen sharing active', result['reasons'])
        self.assertIn('Unknown caller / caller not recognized', result['reasons'])

    def test_run_risk_engine_includes_context_and_final_fusion(self):
        tx = {
            'amount': 15000,
            'beneficiary_new': True,
            'transaction_frequency': 'rare',
            'transaction_time': 'unusual',
            'device_known': False,
            'location_anomaly': True,
            'previous_fraud_history': False,
        }
        behavior = {
            'typing_speed': 'normal',
            'interaction_pattern': 'unusual',
            'device_familiarity': 'unknown',
            'transaction_timing': 'unusual',
            'location_change': 'significant',
            'rapid_repeated_actions': False,
        }
        context = {
            'suspicious_call': True,
            'screen_sharing': False,
            'remote_control': False,
            'unknown_caller': True,
        }
        result = run_risk_engine(tx, voice_transcript='Urgent OTP required now', behavior=behavior, context=context)
        self.assertIn('context', result)
        self.assertIn('final', result)
        self.assertIsInstance(result['final']['score'], int)
        self.assertGreaterEqual(result['final']['score'], 0)
        self.assertLessEqual(result['final']['score'], 100)

    def test_risk_engine_uses_safe_defaults_without_crashing(self):
        tx = {
            'amount': 100,
            'beneficiary_new': False,
            'transaction_frequency': 'regular',
            'transaction_time': 'normal',
            'device_known': True,
            'location_anomaly': False,
            'previous_fraud_history': False,
        }
        result = run_risk_engine(tx, voice_transcript='', behavior=None)
        self.assertEqual(result['final']['level'], 'LOW')


if __name__ == '__main__':
    unittest.main()
