#!/usr/bin/env python3.8


class AppsyncRouterException(Exception):
    pass


class NoRouteFoundException(AppsyncRouterException):
    def __init__(self, *args, **kwargs):
        default_message = "Route does not exist"
        if not (args or kwargs): args = (default_message,)
        super().__init__(*args, **kwargs)


class MultipleRoutesFoundExcepion(AppsyncRouterException):
    def __init__(self, *args, **kwargs):
        default_message = "Multiple matches found for route."
        if not (args or kwargs): args = (default_message,)
        super().__init__(*args, **kwargs)


class RouteAlreadyExistsException(AppsyncRouterException):
    def __init__(self, *args, **kwargs):
        default_message = "Route already exists"
        if not (args or kwargs): args = (default_message,)
        super().__init__(*args, **kwargs)
