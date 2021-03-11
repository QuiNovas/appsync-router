from .router import Router
from pkgutil import walk_packages

resolvers = [x.name for x in walk_packages(path=["resolvers"])]
router = Router()
for x in resolvers:
    exec(f"from resolvers.{x} import *")
