from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version('aprsd-repeat-plugins')
except PackageNotFoundError:
    pass
