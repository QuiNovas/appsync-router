from concurrent.futures import Executor
from typing import Any, Callable, Dict, List, Set, Union

from .exceptions import (
    MultipleRoutesFoundExcepion,
    NoRouteFoundException,
    RouteAlreadyExistsException,
)
from .routes import (
    DiscreteMatch,
    DiscreteRoute,
    GlobMatch,
    GlobRoute,
    MultiRoute,
    PatternMatch,
    PatternRoute,
    Route,
    RouteHandler,
)

__ROUTES: Set[Route] = set()


def add_route(route: Route) -> Route:
    if route:
        if has_route(route):
            raise RouteAlreadyExistsException()
        __ROUTES.add(route)
    return route


def has_route(route: Route) -> bool:
    return route in __ROUTES


def remove_route(route: Route) -> Route:
    try:
        __ROUTES.remove(route)
    except KeyError:
        pass
    return route


def update_route(route: Route) -> Route:
    if route:
        __ROUTES.add(route)
    return route


RouteHandlerDecorator = Callable[[RouteHandler], Route]


def discrete_route(match: DiscreteMatch) -> RouteHandlerDecorator:
    def register_route(handler: RouteHandler) -> Route:
        return add_route(DiscreteRoute(handler=handler, match=match))

    return register_route


def multi_route(matches: Set[DiscreteMatch]) -> RouteHandlerDecorator:
    def register_route(handler: RouteHandler) -> Route:
        return add_route(MultiRoute(handler=handler, matches=matches))

    return register_route


def pattern_route(match: PatternMatch) -> RouteHandlerDecorator:
    def register_route(handler: RouteHandler) -> Route:
        return add_route(PatternRoute(handler=handler, match=match))

    return register_route


def glob_route(match: GlobMatch) -> RouteHandlerDecorator:
    def register_route(handler: RouteHandler) -> Route:
        return add_route(GlobRoute(handler=handler, match=match))

    return register_route


def route_event(
    event: Union[List[Dict], Dict],
    *,
    default_route: Route = Route(),
    executor: Executor = None
) -> Any:
    info = event["info"] if isinstance(event, dict) else event[0]["info"]
    route: Route = None
    context_routes = {route for route in frozenset(__ROUTES) if route.match(info)}
    if not len(context_routes):
        if default_route:
            route = default_route
        raise NoRouteFoundException(info=info)
    elif len(context_routes) == 1:
        route = context_routes.pop()
    else:
        raise MultipleRoutesFoundExcepion(info=info)
    return (
        route(event)
        if isinstance(event, dict)
        else list((executor.map if executor else map)(route, event))
    )
