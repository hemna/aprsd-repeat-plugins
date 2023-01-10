from oslo_config import cfg

from aprsd_repeat_plugins.conf import repeat


CONF = cfg.CONF
repeat.register_opts(CONF)
