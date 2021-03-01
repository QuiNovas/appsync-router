#!/usr/bin/env python3.8
from re import compile, match, Pattern
from fnmatch import fnmatch
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Union,
    Optional
)
from typeguard import typechecked
from .types import (
    Route,
    NamedRoute,
    MatchedRoute,
    GlobbedRoute,
    DefaultRoute,
    Item,
    Response
)
from .exceptions import (
    MultipleRoutesFoundExcepion,
    NoRouteFoundException,
    RouteAlreadyExistsException
)


class Router:
    def __init__(self, allow_multiple_routes=False):
        self.__named_routes = []
        self.__matched_routes = []
        self.__globbed_routes = []
        self.allow_multiple_routes = allow_multiple_routes
        self.default_route = None

    @property
    def named_routes(self):
        return self.__named_routes

    @property
    def matched_routes(self):
        return self._sorted_routes(self.__matched_routes)

    @property
    def globbed_routes(self):
        return self._sorted_routes(self.__globbed_routes)

    @property
    def all_routes(self):
        res = self._sorted_routes([
            *self.named_routes,
            *self.matched_routes,
            *self.globbed_routes
        ], sort_by_paths=True)

        if self.default_route:
            res.append(self.default_route)

        return res

    @property
    def registered_paths(self):
        return [
            (x.path if isinstance(x, NamedRoute) else None) or (x.regex if isinstance(x, MatchedRoute) else None) or x.glob
            for x in self.all_routes
            if not isinstance(x, DefaultRoute)
        ]

    @staticmethod
    def _sorted_routes(routes, sort_by_paths=False):
        def type_sorter(route_type):
            types = {
                "named_route": 1,
                "matched_route": 2,
                "globbed_route": 3,
                "default_route": 4
            }
            return types[route_type]

        if sort_by_paths:
            sorter = lambda x: (
                x.to_dict.get("path") or (x.to_dict.get("regex").pattern if x.to_dict.get("regex") else None) or x.to_dict.get("glob"),
                x.to_dict.get("priority", 0),
                type_sorter(x.type)
            )
        else:
            sorter = lambda x: (
                x.to_dict.get("priority", 0),
                type_sorter(x.type)
            )

        return sorted(routes, key=sorter)

    def get_routes(self, path: str, include_default: Optional[bool] = True, to_dict=False) -> List[Union[Route, Dict]]:
        res = []

        for x in self.__named_routes:
            if x.path == path:
                res.append(x)
                break

        for x in self.__find_matched_route(path, find_all=True):
            res.append(x)

        for x in self.__find_globbed_route(path, find_all=True):
            res.append(x)

        res = self._sorted_routes(res)

        if include_default and self.default_route:
            res.append(self.default_route)

        if to_dict:
            res = [x.to_dict for x in res]

        return res

    @typechecked
    def add_route(self, route: Route) -> Route:
        if isinstance(route, DefaultRoute):
            if self.default_route is not None:
                raise RouteAlreadyExistsException("A default route already exists")
            self.default_route = route
        else:
            if isinstance(route, NamedRoute) and route.path in self.registered_paths:
                raise RouteAlreadyExistsException(f"Route for {route.path} already exists")

            if isinstance(route, MatchedRoute) and route.regex in self.registered_paths:
                raise RouteAlreadyExistsException(f"Route using regex {route.regex} already exists")

            if isinstance(route, GlobbedRoute) and route.glob in self.registered_paths:
                raise RouteAlreadyExistsException(f"Route using glob {route.glob} already exists")

            route_containers = {
                "named_route": self.__named_routes,
                "matched_route": self.__matched_routes,
                "globbed_route": self.__globbed_routes
            }
            route_containers[route.type].append(route)

        return route

    @typechecked
    def remove_route(self, route: Route) -> Route:
        if isinstance(route, DefaultRoute):
            self.default_route = None
        else:
            if route not in self.all_routes:
                raise NoRouteFoundException(f"Route {route} is not in the routing table.")
            route_containers = {
                "named_route": self.__named_routes,
                "matched_route": self.__matched_routes,
                "globbed_route": self.__globbed_routes
            }
            route_containers[route.type].remove(route)

        return route

    @typechecked
    def default(self, func: Callable[[Dict], Any]) -> Callable[[Dict], Any]:
        """
        Sets the default route
        Return value:
        returns a function that must accept a Dict as its sole argument
        """
        if self.default_route is not None:
            raise RouteAlreadyExistsException("A default route has already been registered")

        self.default_route = DefaultRoute(func)

        return func

    @typechecked
    def route(self, path: Union[str, List[str]]) -> Callable[[Dict], Any]:
        """
        Accept a route and return a decorated function after passing that function
        to the Dict of routes to be called by handle_route

        Keyword arguments:
        route: An appsync route expressed as <parent type>.<object type>

        Return value:
        returns a function that must accept a Dict as its sole argument
        """

        if isinstance(path, str):
            paths = [path]
        else:
            paths = path

        for p in paths:
            self.validate_path(p)

        @typechecked
        def inner(func: Callable[[Dict], Any]) -> Callable[[Dict], Any]:
            """
            Accepts a function that accepts a Dict as its sole argument, adds the
            function to the current class object's map of routes to functions,
            and returns the function
            """
            for path in paths:
                self.__named_routes.append(NamedRoute(path, func))

            return func

        return inner

    @typechecked
    def matched_route(self, regex: Union[str, Pattern], priority: Optional[int] = 0) -> Callable[[Dict], Any]:
        """
        Accept a regex to be used for matching routes and return a decorated function after passing
        that function to the Dict of routes to be called by handle_route

        Keyword arguments:
        regex: A string representing a regular expression to match routes against

        Return value:
        returns a function that must accept a Dict as its sole argument
        """
        if isinstance(regex, str):
            regex = compile(regex)

        if regex in self.registered_paths:
            raise RouteAlreadyExistsException(f"Route using regex '{regex}' already exists")

        @typechecked
        def inner(func: Callable[[Dict], Any]) -> Callable[[Dict], Any]:
            """
            Accepts a function that accepts a Dict as its sole argument, adds the
            function to the current class object's map of regexes to functions,
            and returns the function
            """
            self.__matched_routes.append(MatchedRoute(regex, func, priority=priority))

            return func

        return inner

    @typechecked
    def globbed_route(self, glob: str, priority: Optional[int] = 0) -> Callable[[Dict], Any]:
        """
        Accept a glob pattern to be used for matching routes and return a decorated function
        after passing that function to the Dict of routes to be called by handle_route

        Keyword arguments:
        glob: A string used for Unix style glob matching

        Return value:
        returns a function that must accept a Dict as its sole argument
        """

        if glob in self.registered_paths:
            raise RouteAlreadyExistsException(f"Route using glob '{glob}' already exists")

        @typechecked
        def inner(func: Callable[[Dict], Any]) -> Callable[[Dict], Any]:
            """
            Accepts a function that accepts a Dict as its sole argument, adds the
            function to the current class object's map of globs to functions,
            and returns the function
            """
            self.__globbed_routes.append(GlobbedRoute(glob, func, priority=priority))

            return func

        return inner

    @typechecked
    def resolve(self, event: Dict) -> Any:
        """
        Looks up the route for a call based on the parentType and field in event["info"]
        The event arg must, at minimum, contain the info Dict that Appsync places inside of the Lambda event.
        The event arg is the sole argument passed to the route handler. If the route doesn't exist and
        default_route is None, then appsync_tools.exceptions.NonExistentRoute will be raised
        """

        field = event["info"]["parentTypeName"]
        subfield = event["info"]["fieldName"]
        path = f"{field}.{subfield}"

        routes_to_call = self.get_routes(path, include_default=False)

        if len(routes_to_call) > 1 and self.allow_multiple_routes is not True:
            raise MultipleRoutesFoundExcepion(f"Multiple routes match path {path}")

        if len(routes_to_call) == 0:
            if self.default_route is not None:
                routes_to_call = [self.default_route]
            else:
                raise NoRouteFoundException(f"No matching routes for {path}")

        results = Response(path)
        for route in routes_to_call:
            result = route.callable(event)
            item = Item(result, route)
            results.add_item(item)

        return results

    def __find_matched_route(self, path, find_all=False):
        if find_all:
            res = []
        else:
            res = None

        for route in self.matched_routes:
            if match(route.regex, path):
                if find_all:
                    res.append(route)
                else:
                    res = route
                    break

        return res

    def __find_globbed_route(self, path, find_all=False):
        if find_all:
            res = []
        else:
            res = None

        for route in self.globbed_routes:
            if fnmatch(path, route.glob):
                if find_all:
                    res.append(route)
                else:
                    res = route
                    break
        return res

    @typechecked
    def validate_path(self, path: str) -> str:
        if len(path.split(".")) != 2:
            raise ValueError("Explicit routes must take the form of <parentTypeName>.<field>")

        if path in self.__named_routes:
            raise RouteAlreadyExistsException(f"Route for {path} already exists")

        return path
