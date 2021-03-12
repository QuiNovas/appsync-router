from os import path
from pkgutil import walk_packages
from appsync_router import Router, logger

logger.setLevel("DEBUG")

module_dir = path.dirname(__file__)
routes = Router()

resolvers = [x.name for x in walk_packages(path=["resolvers"])]

for x in resolvers:
    exec(f"from .{x} import *")
