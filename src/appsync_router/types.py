from re import Pattern
from typing import Any, Callable, Dict, Union, Optional

from typeguard import typechecked


class Route:
    pass


class NamedRoute(Route):
    def __init__(self, path: str, callable: Callable[[Dict], Any]):
        self.path = path
        self.callable = callable
        self.type = "named_route"
        self.resolver = callable.__module__

    @property
    def to_dict(self):
        return {
            "path": self.path,
            "callable": self.callable,
            "type": "named_route",
            "resolver": self.resolver
        }


class MatchedRoute(Route):
    def __init__(self, regex: Union[str, Pattern], callable: Callable[[Dict], Any], priority: Optional[int] = 0):
        self.regex = regex
        self.callable = callable
        self.priority = priority
        self.type = "matched_route"
        self.resolver = callable.__module__

    @property
    def to_dict(self):
        return {
            "regex": self.regex,
            "callable": self.callable,
            "type": "matched_route",
            "priority": self.priority,
            "resolver": self.resolver
        }


class GlobbedRoute(Route):
    def __init__(self, glob: str, callable: Callable[[Dict], Any], priority: Optional[int] = 0):
        self.glob = glob
        self.callable = callable
        self.priority = priority
        self.type = "globbed_route"
        self.resolver = callable.__module__

    @property
    def to_dict(self):
        return {
            "glob": self.glob,
            "callable": self.callable,
            "type": "globbed_route",
            "priority": self.priority,
            "resolver": self.resolver
        }


class DefaultRoute(Route):
    def __init__(self, callable: Callable[[Dict], Any]):
        self.callable = callable
        self.type = "default_route"
        self.resolver = callable.__module__

    @property
    def to_dict(self):
        return {
            "callable": self.callable,
            "type": "default_route",
            "resolver": self.resolver
        }


class Item:
    def __init__(self, item: Any, route: Route):
        self.value = item
        self.route = route
        self.resolver = route.callable.__module__


class Response:
    def __init__(self, path: str):
        self.path = path
        self.results = []

    @typechecked
    def add_item(self, item: Item):
        self.results.append(item)

    @property
    def values(self) -> list:
        return [
            x.value
            for x in self.results
        ]
