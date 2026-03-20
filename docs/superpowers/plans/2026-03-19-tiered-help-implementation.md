# Tiered Help System Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a tiered help system for APRSD REPEAT plugins with basic (1-2 messages) and full (4-8 messages) help tiers.

**Architecture:** Create a `TieredHelpMixin` base class that `NearestPlugin`, `NearestObjectPlugin`, and `VersionPlugin` inherit from. Create a `RepeatHelpPlugin` that handles `help`, `help <plugin>`, and `help <plugin> full` commands by dispatching to the appropriate `help_basic()` or `help_full()` methods.

**Tech Stack:** Python 3.11+, APRSD plugin framework, unittest

**Spec:** `docs/superpowers/specs/2026-03-19-tiered-help-design.md`

---

## File Structure

| File | Responsibility |
|------|----------------|
| `aprsd_repeat_plugins/help.py` (NEW) | `TieredHelpMixin` base class + `RepeatHelpPlugin` |
| `aprsd_repeat_plugins/nearest.py` (MODIFY) | Add mixin inheritance, implement `help_basic()` and `help_full()` |
| `aprsd_repeat_plugins/version.py` (MODIFY) | Add mixin inheritance, implement `help_basic()` and `help_full()` |
| `tests/test_help.py` (NEW) | Tests for mixin and help plugin |

---

## Chunk 1: TieredHelpMixin Base Class

### Task 1: Create TieredHelpMixin with tests

**Files:**
- Create: `aprsd_repeat_plugins/help.py`
- Create: `tests/test_help.py`

- [ ] **Step 1: Write failing test for TieredHelpMixin interface**

Create `tests/test_help.py`:

```python
#!/usr/bin/env python
"""Tests for tiered help system."""

import unittest

from aprsd_repeat_plugins.help import TieredHelpMixin, MAX_APRS_MSG_LEN


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
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_help.py -v`
Expected: FAIL with "ModuleNotFoundError: No module named 'aprsd_repeat_plugins.help'"

- [ ] **Step 3: Write TieredHelpMixin implementation**

Create `aprsd_repeat_plugins/help.py`:

```python
"""Tiered help system for APRSD REPEAT plugins."""

import abc
import logging

LOG = logging.getLogger('APRSD')

MAX_APRS_MSG_LEN = 67


class TieredHelpMixin(abc.ABC):
    """Mixin providing tiered help for APRS plugins.

    Plugins inherit from this mixin and implement help_basic() and help_full().
    The help() method returns help_basic() for backward compatibility with
    APRSD's built-in HelpPlugin.
    """

    @abc.abstractmethod
    def help_basic(self) -> list[str]:
        """Return 1-2 short messages with syntax and options preview.

        Returns:
            List of help message strings, each <=67 chars for APRS.
        """
        raise NotImplementedError

    @abc.abstractmethod
    def help_full(self) -> list[str]:
        """Return complete reference with all bands, filters, and examples.

        Returns:
            List of help message strings, each <=67 chars for APRS.
        """
        raise NotImplementedError

    def help(self) -> list[str]:
        """Return basic help for backward compatibility.

        This is called by APRSD's built-in HelpPlugin.

        Returns:
            Result of help_basic().
        """
        return self.help_basic()

    def _validate_help_messages(self, messages: list[str]) -> list[str]:
        """Log warning if any message exceeds APRS limit.

        Args:
            messages: List of help message strings.

        Returns:
            The same list of messages (for chaining).
        """
        for msg in messages:
            if len(msg) > MAX_APRS_MSG_LEN:
                LOG.warning(
                    f'Help message exceeds {MAX_APRS_MSG_LEN} chars '
                    f'({len(msg)}): {msg}',
                )
        return messages
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_help.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add aprsd_repeat_plugins/help.py tests/test_help.py
git commit -m "feat: add TieredHelpMixin base class for tiered help system"
```

---

## Chunk 2: RepeatHelpPlugin

### Task 2: Create RepeatHelpPlugin with tests

**Files:**
- Modify: `aprsd_repeat_plugins/help.py`
- Modify: `tests/test_help.py`

- [ ] **Step 1: Write failing tests for RepeatHelpPlugin**

Add to `tests/test_help.py`:

```python
from unittest.mock import MagicMock, patch

from aprsd_repeat_plugins.help import RepeatHelpPlugin


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

        with patch.object(self.plugin, '_get_repeat_plugins', return_value={'nearest': mock_nearest}):
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

        with patch.object(self.plugin, '_get_repeat_plugins', return_value={'nearest': mock_nearest}):
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

        with patch.object(self.plugin, '_get_repeat_plugins', return_value={'nearest': mock_nearest}):
            result = self.plugin.process(packet)

        mock_nearest.help_full.assert_called_once()
        self.assertEqual(result, ['nearest full help line 1', 'line 2'])

    def test_process_unknown_plugin_returns_error(self):
        """Test that 'help unknown' returns error message."""
        packet = MagicMock()
        packet.message_text = 'help unknown'

        mock_nearest = MagicMock()
        mock_nearest.command_name = 'nearest'

        with patch.object(self.plugin, '_get_repeat_plugins', return_value={'nearest': mock_nearest}):
            result = self.plugin.process(packet)

        self.assertIn("Unknown plugin 'unknown'", result)
        self.assertIn('nearest', result)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_help.py::TestRepeatHelpPlugin -v`
Expected: FAIL with "ImportError: cannot import name 'RepeatHelpPlugin'"

- [ ] **Step 3: Write RepeatHelpPlugin implementation**

Add to `aprsd_repeat_plugins/help.py`:

```python
import re

from aprsd import plugin
from oslo_config import cfg

import aprsd_repeat_plugins

CONF = cfg.CONF

# Plugin name to command_name mapping for REPEAT plugins
REPEAT_PLUGINS = {
    'nearest': 'nearest',
    'object': 'object',
    'version': 'version',
    'help': 'help',
}


class RepeatHelpPlugin(TieredHelpMixin, plugin.APRSDRegexCommandPluginBase):
    """Help plugin for APRSD REPEAT service.

    Replaces APRSD's built-in HelpPlugin with tiered help support.
    Handles:
    - help (list available plugins)
    - help <plugin> (basic help for plugin)
    - help <plugin> full (detailed help for plugin)
    """

    version = aprsd_repeat_plugins.__version__
    command_regex = r'^[hH](elp)?'
    command_name = 'help'

    def help_basic(self) -> list[str]:
        return ["help <plugin> or help <plugin> full"]

    def help_full(self) -> list[str]:
        return [
            "help - list available plugins",
            "help <plugin> - basic help for plugin",
            "help <plugin> full - detailed help",
            "plugins: nearest, object, version",
        ]

    def setup(self):
        """Plugin setup."""
        self.enabled = True

    def _parse_help_message(self, message: str) -> tuple[str, str | None, bool]:
        """Parse help message to extract command, plugin name, and full flag.

        Args:
            message: The message text (e.g., "help nearest full")

        Returns:
            Tuple of (command, plugin_name or None, is_full bool)
        """
        parts = message.strip().lower().split()
        cmd = parts[0] if parts else ''
        plugin_name = None
        is_full = False

        if len(parts) >= 2:
            plugin_name = parts[1]
        if len(parts) >= 3 and parts[2] == 'full':
            is_full = True

        return cmd, plugin_name, is_full

    def _get_repeat_plugins(self) -> dict:
        """Get all enabled REPEAT plugins that have TieredHelpMixin.

        Returns:
            Dict mapping command_name to plugin instance.
        """
        from aprsd.plugin import PluginManager

        pm = PluginManager()
        plugins = {}

        for p in pm.get_plugins():
            if (
                p.enabled
                and hasattr(p, 'command_name')
                and isinstance(p, TieredHelpMixin)
                and p.command_name != 'help'  # Exclude self
            ):
                plugins[p.command_name.lower()] = p

        return plugins

    def process(self, packet):
        """Process help command.

        Args:
            packet: APRS message packet.

        Returns:
            Help response string or list of strings.
        """
        LOG.info('RepeatHelpPlugin')

        message = packet.message_text
        _, plugin_name, is_full = self._parse_help_message(message)

        # Get available REPEAT plugins
        plugins = self._get_repeat_plugins()

        if plugin_name is None:
            # User sent just "help" - list available plugins
            plugin_names = sorted(plugins.keys())
            if plugin_names:
                return [
                    "Send 'help <plugin>' or 'help <plugin> full'",
                    f"plugins: {' '.join(plugin_names)}",
                ]
            return "No plugins available"

        # User wants help for a specific plugin
        if plugin_name in plugins:
            p = plugins[plugin_name]
            if is_full:
                return p.help_full()
            return p.help_basic()

        # Unknown plugin
        available = ', '.join(sorted(plugins.keys()))
        return f"Unknown plugin '{plugin_name}'. Available: {available}"
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_help.py -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add aprsd_repeat_plugins/help.py tests/test_help.py
git commit -m "feat: add RepeatHelpPlugin for tiered help dispatch"
```

---

## Chunk 3: Update NearestPlugin with Tiered Help

### Task 3: Add TieredHelpMixin to NearestPlugin

**Files:**
- Modify: `aprsd_repeat_plugins/nearest.py`
- Modify: `tests/test_help.py`

- [ ] **Step 1: Write failing tests for NearestPlugin help methods**

Add to `tests/test_help.py`:

```python
from aprsd_repeat_plugins.nearest import NearestPlugin, NearestObjectPlugin
from aprsd_repeat_plugins.help import MAX_APRS_MSG_LEN


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
                len(msg), MAX_APRS_MSG_LEN,
                f"Message too long ({len(msg)} chars): {msg}"
            )

    def test_help_full_messages_under_limit(self):
        for msg in self.plugin.help_full():
            self.assertLessEqual(
                len(msg), MAX_APRS_MSG_LEN,
                f"Message too long ({len(msg)} chars): {msg}"
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
                len(msg), MAX_APRS_MSG_LEN,
                f"Message too long ({len(msg)} chars): {msg}"
            )

    def test_help_full_messages_under_limit(self):
        for msg in self.plugin.help_full():
            self.assertLessEqual(
                len(msg), MAX_APRS_MSG_LEN,
                f"Message too long ({len(msg)} chars): {msg}"
            )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_help.py::TestNearestPluginHelp -v`
Expected: FAIL with "AssertionError: NearestPlugin is not TieredHelpMixin"

- [ ] **Step 3: Update NearestPlugin to inherit from TieredHelpMixin**

Modify `aprsd_repeat_plugins/nearest.py`:

1. Add import at top:
```python
from aprsd_repeat_plugins.help import TieredHelpMixin
```

2. Change class definition:
```python
class NearestPlugin(
    TieredHelpMixin,
    plugin.APRSDRegexCommandPluginBase,
    plugin.APRSFIKEYMixin,
):
```

3. DELETE the existing `help()` method (around line 133) and replace with:
```python
    def help_basic(self) -> list[str]:
        return [
            "n [#] [band] [+filter] ex: n 3 70cm +echo",
            "bands:2m,70cm,6m,1.25m filters:echo,dmr,dstar",
        ]

    def help_full(self) -> list[str]:
        return [
            "n [#] [band] [+filter] - find nearest repeaters",
            "bands: 2m,70cm,6m,1.25m,33cm,23cm,13cm,9cm,5cm,3cm",
            "filters: echo,irlp,dmr,dstar,ares,races,skywarn",
            "filters: allstar,wires,fm",
            "response: CALL FREQ OFFSET TONE DIST DIR",
            "ex: n 3 70cm +echo (3 70cm echolink repeaters)",
            "ex: n 5 2m +dmr (5 2m DMR repeaters)",
        ]
```

- [ ] **Step 4: Update NearestObjectPlugin help methods**

In `NearestObjectPlugin` class (around line 395), DELETE the existing `help()` method:
```python
    # DELETE THIS METHOD:
    def help(self):
        _help = [
            'object: Return nearest repeaters as APRS object to your last beacon.',
            "object: Send 'o [count] [band] [+filter]'",
            'object: band: example: 2m, 70cm',
            'object: filter: ex: +echo or +irlp',
        ]
        return _help
```

Then ADD the new tiered help methods in its place:
```python
    def help_basic(self) -> list[str]:
        return [
            "o [#] [band] [+filter] ex: o 2 2m +irlp",
            "bands:2m,70cm,6m,1.25m filters:echo,dmr,dstar",
        ]

    def help_full(self) -> list[str]:
        return [
            "o [#] [band] [+filter] - repeaters as APRS objects",
            "bands: 2m,70cm,6m,1.25m,33cm,23cm,13cm,9cm,5cm,3cm",
            "filters: echo,irlp,dmr,dstar,ares,races,skywarn",
            "filters: allstar,wires,fm",
            "ex: o 2 70cm (2 nearest 70cm as objects)",
        ]
```

Note: `NearestObjectPlugin` inherits from `NearestPlugin`, which now inherits from `TieredHelpMixin`. The mixin is acquired through inheritance (Python MRO handles this correctly). By removing the old `help()` method and adding `help_basic()` and `help_full()`, the mixin's `help()` method will be inherited and used (which calls `help_basic()`).

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_help.py -v`
Expected: PASS (all tests)

- [ ] **Step 6: Run existing tests to ensure no regression**

Run: `python -m pytest tests/ -v`
Expected: PASS (all existing tests still pass)

- [ ] **Step 7: Commit**

```bash
git add aprsd_repeat_plugins/nearest.py tests/test_help.py
git commit -m "feat: add tiered help to NearestPlugin and NearestObjectPlugin"
```

---

## Chunk 4: Update VersionPlugin with Tiered Help

### Task 4: Add TieredHelpMixin to VersionPlugin

**Files:**
- Modify: `aprsd_repeat_plugins/version.py`
- Modify: `tests/test_help.py`

- [ ] **Step 1: Write failing tests for VersionPlugin help methods**

Add to `tests/test_help.py`:

```python
from aprsd_repeat_plugins.version import VersionPlugin


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
                len(msg), MAX_APRS_MSG_LEN,
                f"Message too long ({len(msg)} chars): {msg}"
            )

    def test_help_full_messages_under_limit(self):
        for msg in self.plugin.help_full():
            self.assertLessEqual(
                len(msg), MAX_APRS_MSG_LEN,
                f"Message too long ({len(msg)} chars): {msg}"
            )

    def test_help_returns_help_basic(self):
        self.assertEqual(self.plugin.help(), self.plugin.help_basic())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_help.py::TestVersionPluginHelp -v`
Expected: FAIL with "AssertionError: VersionPlugin is not TieredHelpMixin"

- [ ] **Step 3: Update VersionPlugin to inherit from TieredHelpMixin**

Modify `aprsd_repeat_plugins/version.py`:

```python
import logging

from aprsd import plugin

import aprsd_repeat_plugins
from aprsd_repeat_plugins.help import TieredHelpMixin

LOG = logging.getLogger('APRSD')


class VersionPlugin(TieredHelpMixin, plugin.APRSDRegexCommandPluginBase):
    version = aprsd_repeat_plugins.__version__
    # Look for any command that starts with v or V
    command_regex = '^[vV]'
    # the command is for version
    command_name = 'version'

    enabled = False

    def setup(self):
        # Do some checks here?
        self.enabled = True

    def help_basic(self) -> list[str]:
        return ["v - shows REPEAT plugin version"]

    def help_full(self) -> list[str]:
        return ["v or version - shows REPEAT plugin version"]

    def process(self, packet):
        """This is called when a received packet matches self.command_regex."""

        LOG.info('VersionPlugin')

        return f'APRS REPEAT Version: {aprsd_repeat_plugins.__version__}'
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_help.py::TestVersionPluginHelp -v`
Expected: PASS (all tests)

- [ ] **Step 5: Run all tests to ensure no regression**

Run: `python -m pytest tests/ -v`
Expected: PASS (all tests)

- [ ] **Step 6: Commit**

```bash
git add aprsd_repeat_plugins/version.py tests/test_help.py
git commit -m "feat: add tiered help to VersionPlugin"
```

---

## Chunk 5: Integration Test and Documentation

### Task 5: Add integration tests and update README

**Files:**
- Modify: `tests/test_help.py`
- Modify: `README.md`

- [ ] **Step 1: Write integration test for help flow**

Add to `tests/test_help.py`:

```python
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
                    len(msg), MAX_APRS_MSG_LEN,
                    f"{p.command_name} basic help too long ({len(msg)}): {msg}"
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
                    len(msg), MAX_APRS_MSG_LEN,
                    f"{p.command_name} full help too long ({len(msg)}): {msg}"
                )
```

- [ ] **Step 2: Run integration tests**

Run: `python -m pytest tests/test_help.py::TestHelpIntegration -v`
Expected: PASS

- [ ] **Step 3: Update README.md with help usage**

Add the following section to README.md. Insert it after the "### VersionPlugin" section and the "#### Example Interaction" subsection, before the "## Response Format" section:

```markdown
### Help System

The REPEAT plugins include a tiered help system to provide concise or detailed
help over APRS without flooding the network.

#### Basic Help

Send `help <plugin>` for a quick syntax reference (1-2 messages):

```
help nearest
help object
help version
```

#### Detailed Help

Send `help <plugin> full` for complete documentation (4-8 messages):

```
help nearest full
help object full
```

#### RepeatHelpPlugin Configuration

To use the REPEAT help system, enable `RepeatHelpPlugin` and disable APRSD's
built-in HelpPlugin:

```yaml
aprsd:
  enabled_plugins:
    - aprsd_repeat_plugins.help.RepeatHelpPlugin
    - aprsd_repeat_plugins.nearest.NearestPlugin
    - aprsd_repeat_plugins.nearest.NearestObjectPlugin
    - aprsd_repeat_plugins.version.VersionPlugin
```
```

- [ ] **Step 4: Run full test suite**

Run: `python -m pytest tests/ -v`
Expected: PASS (all tests)

- [ ] **Step 5: Commit**

```bash
git add tests/test_help.py README.md
git commit -m "docs: add help system documentation and integration tests"
```

---

## Final Verification

- [ ] **Run full test suite one more time**

Run: `python -m pytest tests/ -v`
Expected: All tests PASS

- [ ] **Run linter**

Run: `tox -e lint` or `ruff check .`
Expected: No errors

- [ ] **Test manually (optional)**

If APRSD is configured locally, test with actual APRS messages:
- Send `help`
- Send `help nearest`
- Send `help nearest full`
- Send `help object`
- Send `help object full`
