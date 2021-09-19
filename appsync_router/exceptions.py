#!/usr/bin/env python3.8
import json
from copy import deepcopy

from .context import Info


class AppsyncRouterException(Exception):
    pass


class RouteHandlingException(AppsyncRouterException):
    def __init__(self, *args, info: Info = None) -> None:
        self.__info = deepcopy(info)
        super().__init__(*args)

    @property
    def info(self) -> Info:
        return self.__info


class NoRouteFoundException(AppsyncRouterException):
    def __init__(self, *args, info: Info = None):
        if not args:
            default_message = "Route does not exist"
            if info:
                default_message += f" for {json.dumps(info, indent=4)}"
            args = (default_message,)
        super().__init__(*args)


class MultipleRoutesFoundException(AppsyncRouterException):
    def __init__(self, *args, info: Info = None):
        if not args:
            default_message = "Multiple matches found"
            if info:
                default_message += f" for {json.dumps(info, indent=4)}"
            args = (default_message,)
        super().__init__(*args)


class RouteAlreadyExistsException(AppsyncRouterException):
    def __init__(self, *args):
        if not args:
            args = ("Route already exists",)
        super().__init__(*args)
