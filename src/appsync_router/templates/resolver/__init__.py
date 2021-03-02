from os import path
from json import load
from pkgutil import walk_packages
from appsync_router import Router


module_dir = path.dirname(__file__)
with open(f"{module_dir}/config.json", "r") as f:
    config = load(f)

routes = Router(**config)

resolvers = [x.name for x in walk_packages(path=["resolvers"])]

for x in resolvers:
    exec(f"from .{x} import *")
