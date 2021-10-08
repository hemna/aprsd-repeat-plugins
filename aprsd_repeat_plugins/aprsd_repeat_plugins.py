import logging

from aprsd import plugin, trace

import aprsd_repeat_plugins


LOG = logging.getLogger("APRSD")


class VersionPlugin(plugin.APRSDRegexCommandPluginBase):

    version = "1.0"
    # Look for any command that starts with w or W
    command_regex = "^[vV]"
    # the command is for ?
    command_name = "version"

    enabled = False

    def setup(self):
        # Do some checks here?
        self.enabled = True

    @trace.trace
    def process(self, packet):
        """This is called when a received packet matches self.command_regex."""

        LOG.info("VersionPlugin")

        return aprsd_repeat_plugins.__version__
