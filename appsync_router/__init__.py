import re
from concurrent.futures import Executor
from functools import partial
from typing import Any, Callable, Union

from multipledispatch import dispatch

from .exceptions import (
    MultipleRoutesFoundException,
    NoRouteFoundException,
    RouteAlreadyExistsException,
)
from .matches import DiscreteMatch, GlobMatch, PatternMatch
from .routes import (
    DiscreteRoute,
    GlobRoute,
    MultiRoute,
    PatternRoute,
    Route,
    RouteHandler,
)

APPSYNC_ROUTER_NAMESPACE = dict()
dispatch = partial(dispatch, namespace=APPSYNC_ROUTER_NAMESPACE)


__ROUTES: set[Route] = set()


def add_route(route: Route) -> Route:
    if route:
        if has_route(route):
            raise RouteAlreadyExistsException()
        __ROUTES.add(route)
    return route


def get_routes() -> frozenset[Route]:
    return frozenset(__ROUTES)


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


RouteHandlerDecorator = Callable[[RouteHandler], RouteHandler]


@dispatch(DiscreteMatch)
def discrete_route(match: DiscreteMatch) -> RouteHandlerDecorator:
    def register_route(handler: RouteHandler) -> RouteHandler:
        add_route(DiscreteRoute(handler=handler, match=match))
        return handler

    return register_route


@dispatch(str, str)
def discrete_route(parentTypeName: str, fieldName: str) -> RouteHandlerDecorator:
    return discrete_route(
        DiscreteMatch(parentTypeName=parentTypeName, fieldName=fieldName)
    )


def multi_route(
    match: Union[DiscreteMatch, tuple[str, str]],
    *matches: Union[DiscreteMatch, tuple[str, str]],
) -> RouteHandlerDecorator:
    _matches = {DiscreteMatch(*match)}
    for match in matches:
        _matches.add(DiscreteMatch(*match))

    def register_route(handler: RouteHandler) -> RouteHandler:
        add_route(MultiRoute(handler=handler, match=_matches))
        return handler

    return register_route


@dispatch(PatternMatch)
def pattern_route(match: PatternMatch) -> RouteHandlerDecorator:
    def register_route(handler: RouteHandler) -> RouteHandler:
        add_route(PatternRoute(handler=handler, match=match))
        return handler

    return register_route


@dispatch(str, str)
def pattern_route(parentTypeName: str, fieldName: str) -> RouteHandlerDecorator:
    return pattern_route(re.compile(parentTypeName), re.compile(fieldName))


@dispatch(re.Pattern, re.Pattern)
def pattern_route(
    parentTypeName: re.Pattern, fieldName: re.Pattern
) -> RouteHandlerDecorator:
    return pattern_route(
        PatternMatch(parentTypeName=parentTypeName, fieldName=fieldName)
    )


@dispatch(str, re.Pattern)
def pattern_route(parentTypeName: str, fieldName: re.Pattern) -> RouteHandlerDecorator:
    return pattern_route(re.compile(parentTypeName), fieldName)


@dispatch(re.Pattern, str)
def pattern_route(parentTypeName: re.Pattern, fieldName: str) -> RouteHandlerDecorator:
    return pattern_route(parentTypeName, re.compile(fieldName))


@dispatch(GlobMatch)
def glob_route(match: GlobMatch) -> RouteHandlerDecorator:
    def register_route(handler: RouteHandler) -> RouteHandler:
        add_route(GlobRoute(handler=handler, match=match))
        return handler

    return register_route


@dispatch(str, str)
def glob_route(parentTypeName: str, fieldName: str) -> RouteHandlerDecorator:
    return glob_route(GlobMatch(parentTypeName=parentTypeName, fieldName=fieldName))


def route_event(
    event: Union[list[dict], dict],
    *,
    default_route: Route = Route(),
    executor: Executor = None,
    short_circuit: bool = True,
) -> Any:
    info = event["info"] if isinstance(event, dict) else event[0]["info"]
    context_route: Route = None
    for route in frozenset(__ROUTES):
        if route.match(info):
            if context_route:
                raise MultipleRoutesFoundException(info=info)
            context_route = route
            if short_circuit:
                break
    if not context_route:
        if default_route:
            context_route = default_route
        else:
            raise NoRouteFoundException(info=info)
    return (
        context_route(event)
        if isinstance(event, dict)
        else list((executor.map if executor else map)(context_route, event))
    )
