from importlib import import_module
from inspect import getmembers
from glob import glob
from appsync_router import Router, logger

logger.setLevel("DEBUG")


def find_packages():
    packages = []
    for x in glob(f"{__name__}/**/*.py", recursive=True):
        pkg_name = x.replace(".py", "").replace("/", ".")
        if pkg_name != f"{__name__}.__init__":
            packages.append(pkg_name)

    return packages


def get_route_handlers():
    package_list = {}
    for package in find_packages():
        pkg_name = package.split(".")[-1]
        pkg_root = ".".join(package.split(".")[:-1])
        mod = import_module(f".{pkg_name}", pkg_root)
        callables = []
        for _, item in getmembers(mod):
            if hasattr(item, "appsync_route"):
                callables.append(item)
        package_list[package] = tuple(callables)

    return package_list


router = Router()
for module, callables in get_route_handlers().items():
    __import__(module, fromlist=[x.__name__ for x in callables])
