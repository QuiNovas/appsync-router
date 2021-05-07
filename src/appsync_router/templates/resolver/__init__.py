from setuptools import find_packages
from importlib import import_module
from inspect import getmembers
from os import path
from pkgutil import walk_packages
from appsync_router import Router, logger

logger.setLevel("DEBUG")


def get_route_handlers():
    resolvers = []
    for p in find_packages("."):
        resolvers += [f"{p}.{x.name}" for x in walk_packages(
            path=[p.replace(".", "/")])]

    package_list = {}

    for package in resolvers:
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
