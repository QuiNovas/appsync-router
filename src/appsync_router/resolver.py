from .router import Router
from pkgutil import walk_packages

resolvers = [x.name for x in walk_packages(path=["resolvers"])]
router = Router(allow_multiple_routes=True)
for x in resolvers:
    exec(f"from resolvers.{x} import *")
