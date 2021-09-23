from __future__ import annotations

import json
import re
from fnmatch import translate
from typing import Any, Callable

from .context import Context, Info
from .matches import DiscreteMatch, GlobMatch, PatternMatch

RouteHandler = Callable[[Context], Any]


class Route:
    def __init__(self, *, handler: RouteHandler = None, match: Any = None) -> None:
        def not_implemented(context: Context):
            raise NotImplementedError(json.dumps(context["info"], indent=4))

        self.__handler = handler or not_implemented
        self.__match = match
        super().__init__()

    def __hash__(self) -> int:
        return hash(self.__match)

    def __call__(self, context: Context) -> Any:
        return self.__handler(context)

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.__match} -> {self.__handler.__module__}.{self.__handler.__name__}"

    @property
    def _handler(self) -> RouteHandler:
        return self.__handler

    @property
    def _match(self) -> Any:
        return self.__match

    def match(self, /, info: Info) -> bool:
        return True


class DiscreteRoute(Route):
    def __init__(self, *, handler: RouteHandler, match: DiscreteMatch) -> None:
        super().__init__(handler=handler, match=match)

    @property
    def _match(self) -> DiscreteMatch:
        return super()._match

    def match(self, /, info: Info) -> bool:
        return (
            DiscreteMatch(
                parentTypeName=info["parentTypeName"], fieldName=info["fieldName"]
            )
            == self._match
        )


class MultiRoute(Route):
    def __init__(self, *, handler: RouteHandler, match: set[DiscreteMatch]) -> None:
        super().__init__(handler=handler, match=frozenset(match))

    @property
    def _match(self) -> set[DiscreteMatch]:
        return super()._match

    def match(self, /, info: Info) -> bool:
        return (
            DiscreteMatch(
                parentTypeName=info["parentTypeName"], fieldName=info["fieldName"]
            )
            in self._match
        )


class PatternRoute(Route):
    def __init__(self, *, handler: RouteHandler, match: PatternMatch) -> None:
        super().__init__(handler=handler, match=match)

    @property
    def _match(self) -> PatternMatch:
        return super()._match

    def match(self, /, info: Info) -> bool:
        return self._match.parentTypeName.match(
            info["parentTypeName"]
        ) and self._match.fieldName.match(info["fieldName"])


class GlobRoute(PatternRoute):
    def __init__(self, *, handler: RouteHandler, match: GlobMatch) -> None:
        self.__glob_match = match
        super().__init__(
            handler=handler,
            match=PatternMatch(
                fieldName=re.compile(translate(match.fieldName)),
                parentTypeName=re.compile(translate(match.parentTypeName)),
            ),
        )

    def __str__(self) -> str:
        return f"{type(self).__name__}: {self.__glob_match} -> {self._handler.__module__}.{self._handler.__name__}"
