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
