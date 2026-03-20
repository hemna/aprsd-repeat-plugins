#!/usr/bin/env python
"""Tests for tiered help system."""

import unittest

from aprsd_repeat_plugins.help import MAX_APRS_MSG_LEN, TieredHelpMixin


class MockPlugin(TieredHelpMixin):
    """Mock plugin for testing mixin."""

    command_name = 'mock'

    def help_basic(self):
        return ['mock: basic help']

    def help_full(self):
        return ['mock: full help line 1', 'mock: full help line 2']


class TestTieredHelpMixin(unittest.TestCase):
    def setUp(self):
        self.plugin = MockPlugin()

    def test_help_basic_returns_list(self):
        result = self.plugin.help_basic()
        self.assertIsInstance(result, list)
        self.assertEqual(result, ['mock: basic help'])

    def test_help_full_returns_list(self):
        result = self.plugin.help_full()
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)

    def test_help_returns_help_basic_for_backward_compat(self):
        result = self.plugin.help()
        self.assertEqual(result, self.plugin.help_basic())

    def test_max_aprs_msg_len_constant(self):
        self.assertEqual(MAX_APRS_MSG_LEN, 67)

    def test_validate_help_messages_logs_warning_for_long_message(self):
        """Test that _validate_help_messages logs warning for messages > 67 chars."""
        long_msg = 'x' * 70  # 70 chars, exceeds 67 limit
        with self.assertLogs('APRSD', level='WARNING') as log:
            self.plugin._validate_help_messages([long_msg])
        self.assertTrue(any('exceeds 67 chars' in msg for msg in log.output))

    def test_validate_help_messages_no_warning_for_short_message(self):
        """Test that _validate_help_messages does not warn for messages <= 67 chars."""
        short_msg = 'x' * 67  # Exactly 67 chars, at limit
        # Should not raise any warnings
        result = self.plugin._validate_help_messages([short_msg])
        self.assertEqual(result, [short_msg])


if __name__ == '__main__':
    unittest.main()
