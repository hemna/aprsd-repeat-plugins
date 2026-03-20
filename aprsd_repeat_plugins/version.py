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
        return ['v - shows REPEAT plugin version']

    def help_full(self) -> list[str]:
        return ['v or version - shows REPEAT plugin version']

    def process(self, packet):
        """This is called when a received packet matches self.command_regex."""

        LOG.info('VersionPlugin')

        return f'APRS REPEAT Version: {aprsd_repeat_plugins.__version__}'
