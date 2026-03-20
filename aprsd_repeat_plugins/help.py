"""Tiered help system for APRSD REPEAT plugins."""

import abc
import logging

from aprsd import plugin

import aprsd_repeat_plugins

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
            Result of help_basic(), validated for message length.
        """
        return self._validate_help_messages(self.help_basic())

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
        return ['help <plugin> or help <plugin> full']

    def help_full(self) -> list[str]:
        return [
            'help - list available plugins',
            'help <plugin> - basic help for plugin',
            'help <plugin> full - detailed help',
        ]

    def setup(self):
        """Plugin setup."""
        self.enabled = True

    def _parse_help_message(self, message: str) -> tuple[str | None, bool]:
        """Parse help message to extract plugin name and full flag.

        Args:
            message: The message text (e.g., "help nearest full")

        Returns:
            Tuple of (plugin_name or None, is_full bool)
        """
        parts = message.strip().lower().split()
        plugin_name = None
        is_full = False

        if len(parts) >= 2:
            plugin_name = parts[1]
        if len(parts) >= 3 and parts[2] == 'full':
            is_full = True

        return plugin_name, is_full

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
        plugin_name, is_full = self._parse_help_message(message)

        # Get available REPEAT plugins
        plugins = self._get_repeat_plugins()

        if plugin_name is None:
            # User sent just "help" - list available plugins
            plugin_names = sorted(plugins.keys())
            if plugin_names:
                return [
                    "Send 'help <plugin>' or 'help <plugin> full'",
                    f'plugins: {" ".join(plugin_names)}',
                ]
            return 'No plugins available'

        # User wants help for a specific plugin
        if plugin_name in plugins:
            p = plugins[plugin_name]
            if is_full:
                return self._validate_help_messages(p.help_full())
            return self._validate_help_messages(p.help_basic())

        # Unknown plugin - handle empty plugins case
        if plugins:
            available = ', '.join(sorted(plugins.keys()))
            return f"Unknown plugin '{plugin_name}'. Available: {available}"
        return f"Unknown plugin '{plugin_name}'. No plugins available"
