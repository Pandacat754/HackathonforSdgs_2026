import unittest
from unittest.mock import patch
import live_evaluation


class EvaluationTests(unittest.TestCase):
    def test_fallback_never_counts_as_success(self):
        def failing(message, **kwargs):
            self.assertNotIn('expected_category', message)
            return {'category': 'needs_human_review', 'action': 'ask_user_to_review',
                    'source': 'fallback', 'error_code': 'failure', 'requires_user_confirmation': True,
                    'suggested_reply': None}
        with patch('builtins.print'):
            records = live_evaluation.run_cases(failing)
        self.assertEqual(len(records), 16)
        self.assertFalse(any(record['passed'] for record in records))

    def test_no_key_sends_nothing(self):
        with patch.dict('os.environ', {}, clear=True), patch('live_evaluation.run_cases') as run, patch('builtins.print'):
            self.assertEqual(live_evaluation.main(), 2)
            run.assert_not_called()
