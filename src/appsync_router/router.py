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
    """
    Creates routes from Appsync paths, expressed as *<event["info"]["parentTypeName"]>.<event["info"]["fieldName"]>*,
    to callables specied by supplied decorators or explicit calls to appsync_router.Router.add_route()
    """

    def __init__(self):
        self.__named_routes = []
        self.__matched_routes = []
        self.__globbed_routes = []
        #: An instance of ``appsync_router.Route`` that will be used when the path is not resolved by any other route
        self.default_route = None

    @property
    def named_routes(self):
        """
        Returns a list containing all routes of type appsync_router.NamedRoute
        that are currently registered.

        :returns:
            ``list``
        """
        return self.__named_routes

    @property
    def matched_routes(self):
        """
        Returns a list containing all routes of type appsync_router.MatchedRoute
        that are currently registered.

        :returns:
            ``list``
        """
        return self._sorted_routes(self.__matched_routes)

    @property
    def globbed_routes(self):
        """
        Returns a list containing all routes of type appsync_router.GlobbedRoute
        that are currently registered.

        :returns:
            ``list``
        """
        return self._sorted_routes(self.__globbed_routes)

    @property
    def all_routes(self):
        """
        Returns a list containing all registered routes

        :returns:
            ``list``
        """

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
        """
        Returns a list containing all registered paths

        :returns:
            ``list``
        """

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
        """
        Returns all registered routes that match *path*

        :params:
            * *path:* (``str``): The path to check routes against

        :Keyword Arguments:
            * *include_default:* (``bool``) - If True will return self.default_route, if one is registered
            * *to_dict:* (``bool``) - Return routes as a list of dicts instead of objects

        :returns:
            ``list``

        """
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
        """
        Registers a route

        :params:
            * *route*: (``Route``): An instance of NamedRoute, MatchedRoute or GlobbedRoute to register

        :returns:
            ``appsync_router.Route``
        """

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
        """
        Removes a route

        :params:
            * *route:* (``Route``): An instance of appsync_tools.Route

        :returns:
            ``appsync_router.Route``
        """

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
        Used as a decorator to set ``self.default_route``. If ``self.default_route`` is set.

        :returns:
            ``Callable``
        """
        if self.default_route is not None:
            raise RouteAlreadyExistsException("A default route has already been registered")

        self.default_route = DefaultRoute(func)

        return func

    @typechecked
    def route(self, path: Union[str, List[str]]) -> Callable[[Dict], Any]:
        """
        Used as a decorator to register a function as an appsync_router.NamedRoute

        :Keyword Arguments:
            * *path:* (``str``): An appsync path expressed as ``<parent type name>.<field name>``

        :returns:
            ``Callable``
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
        Used as a decorator to register an appsync_router.MatchedRoute

        :Keyword Arguments:
            * *regex:* (``str|re.Pattern``): A regex string pattern or instance of re.Pattern to match routes against
            * *priority:* (``int``): An optional priority to set on the route. See the section on priorities for more

        :returns:
            ``Callable``
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
        Used as a decorator to register an appsync_router.GlobbedRoute

        :Keyword Arguments:
            * *glob:* (``str``): A Unix-style glob pattern to match routes against
            * *priority:* (``int``): An optional priority to set on the route. See the section on priorities for more

        :returns:
            ``Callable``
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
    def resolve(self, event: Any) -> Item:
        """
        Looks up the route for a call based on the parentTypeName and fieldName in event["info"]. If ``self.chain`` is True then the first route will be passed ``event``
        and any subsequent matches will be passed the result of the prior route. If the path doesn't match a registered route and ``self.default_route`` is None, then
        ``appsync_tools.exceptions.NonExistentRoute`` will be raised.

        :params:
            * *event:* An event that matches the format passed to Lambda from an appsync call. The event arg must, at minimum, contain the info Dict that Appsync places inside of the Lambda event.

        :returns:
            ``appsync_router.Item``
        """

        field = event["info"]["parentTypeName"]
        subfield = event["info"]["fieldName"]
        path = f"{field}.{subfield}"

        matched_routes = self.get_routes(path, include_default=False)

        if len(matched_routes) > 1:
            raise MultipleRoutesFoundExcepion(f"Multiple routes match path {path}")

        if len(matched_routes) == 0:
            if self.default_route is not None:
                matched_routes = [self.default_route]
            else:
                raise NoRouteFoundException(f"No matching routes for {path}")

        route = matched_routes[0]

        res = Item(
            route.callable(event),
            route
        )

        return res

    @typechecked
    def resolve_all(self, event: Any, chain=False) -> Response:
        """
        Looks up the route for a call based on the parentTypeName and fieldName in event["info"]. If ``chain`` is True then the first route will be passed ``event``
        and any subsequent matches will be passed the result of the prior route. If the path doesn't match a registered route and ``self.default_route`` is None, then
        ``appsync_tools.exceptions.NonExistentRoute`` will be raised.

        :params:
            * *event:* (``dict``) - An event that matches the format passed to Lambda from Appsync. The event arg must, at minimum, contain the info Dict that Appsync places inside event.
            * *chain:* (``bool``): If True then as then the first resolved route will accept ``event`` whith each subsequent matched route being passed the result of the prior

        :returns:
            ``appsync_router.Response``
        """

        field = event["info"]["parentTypeName"]
        subfield = event["info"]["fieldName"]
        path = f"{field}.{subfield}"

        routes_to_call = self.get_routes(path, include_default=False)

        if len(routes_to_call) == 0:
            if self.default_route is not None:
                routes_to_call = [self.default_route]
            else:
                raise NoRouteFoundException(f"No matching routes for {path}")

        results = Response(path, chained=self.chain)
        for route in routes_to_call:
            result = route.callable(event)
            if self.chain is True:
                event = result
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
        """
        Raises an exception if a path is invalid or already exists

        :params:
            * *path:* (``str``): An Appsync path

        :returns:
            ``str``
        """

        if len(path.split(".")) != 2:
            raise ValueError("Explicit routes must take the form of <parentTypeName>.<field>")

        if path in self.__named_routes:
            raise RouteAlreadyExistsException(f"Route for {path} already exists")

        return path
