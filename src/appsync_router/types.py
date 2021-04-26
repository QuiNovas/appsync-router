from re import Pattern
from collections.abc import MutableMapping
from typing import Any, Callable, Dict, Union, Optional
from typeguard import typechecked


class Route(MutableMapping):
    def __init__(self):
        super().__init__()

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        '''returns simple dict representation of the mapping'''
        return str(self.__dict__)


class NamedRoute(Route):
    def __init__(self, path: str, callable: Callable[[Dict], Any]):
        super().__init__()

        #: Path to resolve
        self.path = path
        #: Callable registered to this path
        self.callable = callable
        #: Describes the type of Route
        self.type = "named_route"
        #: The module name that self.callable is part of
        self.resolver = callable.__module__

    @property
    def to_dict(self):
        """Casts all available properties to items in a dictionary"""
        return {
            "path": self.path,
            "callable": self.callable,
            "type": "named_route",
            "resolver": self.resolver
        }


class MatchedRoute(Route):
    def __init__(self, regex: Union[str, Pattern], callable: Callable[[Dict], Any], priority: Optional[int] = 0):
        #: The regex used to match a path
        self.regex = regex
        #: The callable registered to this path
        self.callable = callable
        #: The priority (order) this Route will be in when multiple routes match a path
        self.priority = priority
        #: Description of the type of Route
        self.type = "matched_route"
        #: The module name that self.callable is part of
        self.resolver = callable.__module__

    @property
    def to_dict(self):
        """Casts all available properties to items in a dictionary"""
        return {
            "regex": self.regex,
            "callable": self.callable,
            "type": "matched_route",
            "priority": self.priority,
            "resolver": self.resolver
        }


class GlobbedRoute(Route):
    def __init__(self, glob: str, callable: Callable[[Dict], Any], priority: Optional[int] = 0):
        #: A Unix-style glob pattern for patching paths
        self.glob = glob
        #: The callable registered to this path
        self.callable = callable
        #: The priority (order) this Route will be in when multiple routes match a path
        self.priority = priority
        #: Description of the type of Route
        self.type = "globbed_route"
        #: The module name that self.callable is part of
        self.resolver = callable.__module__

    @property
    def to_dict(self):
        """Casts all available properties to items in a dictionary"""
        return {
            "glob": self.glob,
            "callable": self.callable,
            "type": "globbed_route",
            "priority": self.priority,
            "resolver": self.resolver
        }


class DefaultRoute(Route):
    def __init__(self, callable: Callable[[Dict], Any]):
        #: The callable registered for the default_route
        self.callable = callable
        #: A description of the Route type
        self.type = "default_route"
        #: The module name that self.callable is part of
        self.resolver = callable.__module__

    @property
    def to_dict(self):
        """Casts all available properties to items in a dictionary"""
        return {
            "callable": self.callable,
            "type": "default_route",
            "resolver": self.resolver
        }


class Item(MutableMapping):
    """An object containing the response from a Route's callable and information about the Route"""

    value: Any
    route: str
    resolver: Any

    def __init__(self, item: Any, route: Route):
        super().__init__()
        #: The value returned by the callable for self.route
        self.value = item
        #: The Route that matched the path passed to appsync_router.Router.resolve
        self.route = route
        #: The module that this resolver's callable belongs to
        self.resolver = route.callable.__module__

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        '''returns simple dict representation of the mapping'''
        return str(self.__dict__)


class Response:
    """An object containing a list of appsync_router.types.Item"""
    def __init__(self, path: str, chained: bool = False):
        super().__init__()

        #: The path that triggered this Response
        self.path = path
        #: A list of Item
        self.results = []
        self.chained = chained

    @typechecked
    def add_item(self, item: Item):
        """Adds an **Item** to **Response** object"""
        self.results.append(item)

    @property
    def values(self) -> list:
        """Returns a list containing the value attribute of all **Items** in **Response**"""
        if self.results:
            return [
                x.value
                for x in self.results
            ]

    @property
    def final(self) -> Item:
        """Returns a list containing the value attribute of all **Items** in **Response**"""
        if self.results:
            return self.results[-1]

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    def __getitem__(self, key):
        return self.__dict__[key]

    def __delitem__(self, key):
        del self.__dict__[key]

    def __iter__(self):
        return iter(self.__dict__)

    def __len__(self):
        return len(self.__dict__)

    def __str__(self):
        '''returns simple dict representation of the mapping'''
        return str(self.__dict__)


@typechecked
class Stash(dict):
    def __init__(self, stash: Optional[dict] = {}):
        for k, v in stash.items():
            self[k] = v

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = Stash(value)

        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)

    def __iter__(self):
        return dict.__iter__(self)

    def __len__(self):
        return dict.__len__(self)

    def __contains__(self, x):
        return dict.__contains__(self, x)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __getattribute__(self, name):
        if name in self:
            return self[name]
        elif getattr(dict, name, None) and callable(dict.__getattribute__(self, name)):
            return dict.__getattribute__(self, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")


@typechecked
class Event(dict):
    def __init__(self, event: dict = {}):
        for k, v in event.items():
            self[k] = v

    def __getitem__(self, key):
        return dict.__getitem__(self, key)

    def __setitem__(self, key, value):
        if isinstance(value, dict):
            value = Stash(value)

        dict.__setitem__(self, key, value)

    def __delitem__(self, key):
        dict.__delitem__(self, key)

    def __iter__(self):
        return dict.__iter__(self)

    def __len__(self):
        return dict.__len__(self)

    def __contains__(self, x):
        return dict.__contains__(self, x)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError as k:
            raise AttributeError(k)

    def __getattribute__(self, name):
        if name in self:
            return self[name]
        elif getattr(dict, name, None) and callable(dict.__getattribute__(self, name)):
            return dict.__getattribute__(self, name)
        else:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
