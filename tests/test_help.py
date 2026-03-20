#!/usr/bin/env python
"""Tests for tiered help system."""

import unittest
from unittest.mock import MagicMock, patch

from aprsd_repeat_plugins.help import (
    MAX_APRS_MSG_LEN,
    RepeatHelpPlugin,
    TieredHelpMixin,
)
from aprsd_repeat_plugins.nearest import NearestObjectPlugin, NearestPlugin
from aprsd_repeat_plugins.version import VersionPlugin


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


class TestRepeatHelpPlugin(unittest.TestCase):
    def setUp(self):
        self.plugin = RepeatHelpPlugin()

    def test_command_regex_matches_help(self):
        import re

        pattern = re.compile(self.plugin.command_regex)
        self.assertIsNotNone(pattern.match('help'))
        self.assertIsNotNone(pattern.match('Help'))
        self.assertIsNotNone(pattern.match('h'))
        self.assertIsNotNone(pattern.match('H'))

    def test_command_name(self):
        self.assertEqual(self.plugin.command_name, 'help')

    def test_help_basic_returns_list(self):
        result = self.plugin.help_basic()
        self.assertIsInstance(result, list)

    def test_help_full_returns_list(self):
        result = self.plugin.help_full()
        self.assertIsInstance(result, list)


class TestRepeatHelpPluginParsing(unittest.TestCase):
    def setUp(self):
        self.plugin = RepeatHelpPlugin()

    def test_parse_help_alone(self):
        cmd, plugin_name, is_full = self.plugin._parse_help_message('help')
        self.assertEqual(cmd, 'help')
        self.assertIsNone(plugin_name)
        self.assertFalse(is_full)

    def test_parse_help_plugin(self):
        cmd, plugin_name, is_full = self.plugin._parse_help_message('help nearest')
        self.assertEqual(cmd, 'help')
        self.assertEqual(plugin_name, 'nearest')
        self.assertFalse(is_full)

    def test_parse_help_plugin_full(self):
        cmd, plugin_name, is_full = self.plugin._parse_help_message('help nearest full')
        self.assertEqual(cmd, 'help')
        self.assertEqual(plugin_name, 'nearest')
        self.assertTrue(is_full)

    def test_parse_h_shorthand(self):
        cmd, plugin_name, is_full = self.plugin._parse_help_message('h')
        self.assertEqual(cmd, 'h')
        self.assertIsNone(plugin_name)
        self.assertFalse(is_full)

    def test_parse_h_plugin(self):
        cmd, plugin_name, is_full = self.plugin._parse_help_message('h nearest')
        self.assertEqual(cmd, 'h')
        self.assertEqual(plugin_name, 'nearest')
        self.assertFalse(is_full)


class TestRepeatHelpPluginProcess(unittest.TestCase):
    """Tests for RepeatHelpPlugin.process() dispatch logic."""

    def setUp(self):
        self.plugin = RepeatHelpPlugin()

    def test_process_help_alone_returns_plugin_list(self):
        """Test that 'help' alone lists available plugins."""
        packet = MagicMock()
        packet.message_text = 'help'

        # Mock _get_repeat_plugins to return known plugins
        mock_nearest = MagicMock()
        mock_nearest.command_name = 'nearest'
        mock_nearest.help_basic.return_value = ['nearest help']

        with patch.object(
            self.plugin, '_get_repeat_plugins', return_value={'nearest': mock_nearest}
        ):
            result = self.plugin.process(packet)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 2)
        self.assertIn('plugins:', result[1])

    def test_process_help_plugin_returns_basic_help(self):
        """Test that 'help nearest' returns basic help."""
        packet = MagicMock()
        packet.message_text = 'help nearest'

        mock_nearest = MagicMock()
        mock_nearest.command_name = 'nearest'
        mock_nearest.help_basic.return_value = ['nearest basic help']

        with patch.object(
            self.plugin, '_get_repeat_plugins', return_value={'nearest': mock_nearest}
        ):
            result = self.plugin.process(packet)

        mock_nearest.help_basic.assert_called_once()
        self.assertEqual(result, ['nearest basic help'])

    def test_process_help_plugin_full_returns_full_help(self):
        """Test that 'help nearest full' returns full help."""
        packet = MagicMock()
        packet.message_text = 'help nearest full'

        mock_nearest = MagicMock()
        mock_nearest.command_name = 'nearest'
        mock_nearest.help_full.return_value = ['nearest full help line 1', 'line 2']

        with patch.object(
            self.plugin, '_get_repeat_plugins', return_value={'nearest': mock_nearest}
        ):
            result = self.plugin.process(packet)

        mock_nearest.help_full.assert_called_once()
        self.assertEqual(result, ['nearest full help line 1', 'line 2'])

    def test_process_unknown_plugin_returns_error(self):
        """Test that 'help unknown' returns error message."""
        packet = MagicMock()
        packet.message_text = 'help unknown'

        mock_nearest = MagicMock()
        mock_nearest.command_name = 'nearest'

        with patch.object(
            self.plugin, '_get_repeat_plugins', return_value={'nearest': mock_nearest}
        ):
            result = self.plugin.process(packet)

        self.assertIn("Unknown plugin 'unknown'", result)
        self.assertIn('nearest', result)

    def test_process_help_no_plugins_returns_message(self):
        """Test that 'help' with no plugins returns appropriate message."""
        packet = MagicMock()
        packet.message_text = 'help'

        with patch.object(self.plugin, '_get_repeat_plugins', return_value={}):
            result = self.plugin.process(packet)

        self.assertEqual(result, 'No plugins available')


class TestNearestPluginHelp(unittest.TestCase):
    def setUp(self):
        self.plugin = NearestPlugin()

    def test_is_tiered_help_mixin(self):
        self.assertIsInstance(self.plugin, TieredHelpMixin)

    def test_help_basic_returns_list(self):
        result = self.plugin.help_basic()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)
        self.assertLessEqual(len(result), 2)

    def test_help_full_returns_list(self):
        result = self.plugin.help_full()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 4)

    def test_help_basic_messages_under_limit(self):
        for msg in self.plugin.help_basic():
            self.assertLessEqual(
                len(msg),
                MAX_APRS_MSG_LEN,
                f'Message too long ({len(msg)} chars): {msg}',
            )

    def test_help_full_messages_under_limit(self):
        for msg in self.plugin.help_full():
            self.assertLessEqual(
                len(msg),
                MAX_APRS_MSG_LEN,
                f'Message too long ({len(msg)} chars): {msg}',
            )

    def test_help_returns_help_basic(self):
        self.assertEqual(self.plugin.help(), self.plugin.help_basic())


class TestNearestObjectPluginHelp(unittest.TestCase):
    def setUp(self):
        self.plugin = NearestObjectPlugin()

    def test_is_tiered_help_mixin(self):
        self.assertIsInstance(self.plugin, TieredHelpMixin)

    def test_help_basic_returns_list(self):
        result = self.plugin.help_basic()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)
        self.assertLessEqual(len(result), 2)

    def test_help_full_returns_list(self):
        result = self.plugin.help_full()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 4)

    def test_help_basic_messages_under_limit(self):
        for msg in self.plugin.help_basic():
            self.assertLessEqual(
                len(msg),
                MAX_APRS_MSG_LEN,
                f'Message too long ({len(msg)} chars): {msg}',
            )

    def test_help_full_messages_under_limit(self):
        for msg in self.plugin.help_full():
            self.assertLessEqual(
                len(msg),
                MAX_APRS_MSG_LEN,
                f'Message too long ({len(msg)} chars): {msg}',
            )

    def test_help_returns_help_basic(self):
        self.assertEqual(self.plugin.help(), self.plugin.help_basic())


class TestVersionPluginHelp(unittest.TestCase):
    def setUp(self):
        self.plugin = VersionPlugin()

    def test_is_tiered_help_mixin(self):
        self.assertIsInstance(self.plugin, TieredHelpMixin)

    def test_help_basic_returns_list(self):
        result = self.plugin.help_basic()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)

    def test_help_full_returns_list(self):
        result = self.plugin.help_full()
        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)

    def test_help_basic_messages_under_limit(self):
        for msg in self.plugin.help_basic():
            self.assertLessEqual(
                len(msg),
                MAX_APRS_MSG_LEN,
                f'Message too long ({len(msg)} chars): {msg}',
            )

    def test_help_full_messages_under_limit(self):
        for msg in self.plugin.help_full():
            self.assertLessEqual(
                len(msg),
                MAX_APRS_MSG_LEN,
                f'Message too long ({len(msg)} chars): {msg}',
            )

    def test_help_returns_help_basic(self):
        self.assertEqual(self.plugin.help(), self.plugin.help_basic())


class TestHelpIntegration(unittest.TestCase):
    """Integration tests for the full help flow."""

    def test_all_basic_help_messages_under_limit(self):
        """Verify all plugins have compliant basic help messages."""
        plugins = [
            NearestPlugin(),
            NearestObjectPlugin(),
            VersionPlugin(),
            RepeatHelpPlugin(),
        ]
        for p in plugins:
            for msg in p.help_basic():
                self.assertLessEqual(
                    len(msg),
                    MAX_APRS_MSG_LEN,
                    f'{p.command_name} basic help too long ({len(msg)}): {msg}',
                )

    def test_all_full_help_messages_under_limit(self):
        """Verify all plugins have compliant full help messages."""
        plugins = [
            NearestPlugin(),
            NearestObjectPlugin(),
            VersionPlugin(),
            RepeatHelpPlugin(),
        ]
        for p in plugins:
            for msg in p.help_full():
                self.assertLessEqual(
                    len(msg),
                    MAX_APRS_MSG_LEN,
                    f'{p.command_name} full help too long ({len(msg)}): {msg}',
                )


if __name__ == '__main__':
    unittest.main()
