from oslo_config import cfg


repeat_group = cfg.OptGroup(
    name="aprsd_repeat_plugins",
    title="APRSD REPEAT Plugin settings",
)

repeat_opts = [
    cfg.StrOpt(
        "haminfo_apiKey",
        help="Haminfo API key",
    ),
    cfg.StrOpt(
        "haminfo_base_url",
        help="The base url to the haminfo REST API",
    ),
]

ALL_OPTS = (
    repeat_opts
)


def register_opts(cfg):
    cfg.register_group(repeat_group)
    cfg.register_opts(ALL_OPTS, group=repeat_group)


def list_opts():
    register_opts(cfg.CONF)
    return {
        repeat_group.name: ALL_OPTS,
    }
