from __future__ import annotations

import json
import re
from fnmatch import translate
from typing import Any, Callable, NamedTuple, Pattern, Set, Union

from .context import Context, Info

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
        return self.__handler(context=context)

    @property
    def _match(self) -> Any:
        return self.__match

    def match(self, /, info: Info) -> bool:
        return True


class DiscreteMatch(NamedTuple):
    fieldName: str
    parentTypeName: str


class DiscreteRoute(Route):
    def __init__(self, *, handler: RouteHandler, match: DiscreteMatch) -> None:
        super().__init__(handler=handler, match=match)

    @property
    def _match(self) -> DiscreteMatch:
        return super()._match

    def match(self, /, info: Info) -> bool:
        return (
            DiscreteMatch(
                fieldName=info["fieldName"], parentTypeName=info["parentTypeName"]
            )
            == self._match
        )


class MultiRoute(Route):
    def __init__(self, *, handler: RouteHandler, matches: Set[DiscreteMatch]) -> None:
        super().__init__(handler=handler, match=frozenset(matches))

    @property
    def _match(self) -> Set[DiscreteMatch]:
        return super()._match

    def match(self, /, info: Info) -> bool:
        return (
            DiscreteMatch(
                fieldName=info["fieldName"], parentTypeName=info["parentTypeName"]
            )
            in self._match
        )


class PatternMatch(NamedTuple):
    fieldName: Union[re.Pattern, str]
    parentTypeName: Union[re.Pattern, str]

    def __str__(self) -> str:
        field_name = (
            self.fieldName.pattern
            if isinstance(self.fieldName, re.Pattern)
            else self.fieldName
        )
        parent_type_name = (
            self.parentTypeName.pattern
            if isinstance(self.parentTypeName, re.Pattern)
            else self.parentTypeName
        )
        return f'PatternMatch(fieldName="{field_name}", parentTypeName="{parent_type_name}"'


class PatternRoute(Route):
    def __init__(self, *, handler: RouteHandler, match: PatternMatch) -> None:
        if not (
            isinstance(match.parentTypeName, re.Pattern)
            and isinstance(match.fieldName, re.Pattern)
        ):
            match = PatternMatch(
                fieldName=match.fieldName
                if isinstance(match.fieldName, re.Pattern)
                else re.compile(match.fieldName),
                parentTypeName=match.parentTypeName
                if isinstance(match.parentTypeName, re.Pattern)
                else re.compile(match.parentTypeName),
            )
        super().__init__(handler=handler, match=match)

    @property
    def _match(self) -> PatternMatch:
        return super()._match

    def match(self, /, info: Info) -> bool:
        return self._match.parentTypeName.match(
            info["parentTypeName"]
        ) and self._match.fieldName.match(info["fieldName"])


class GlobMatch(NamedTuple):
    fieldName: str
    parentTypeName: str


class GlobRoute(PatternRoute):
    def __init__(self, *, handler: RouteHandler, match: GlobMatch) -> None:
        super().__init__(
            handler=handler,
            match=PatternMatch(
                fieldName=re.compile(translate(match.fieldName)),
                parentTypeName=re.compile(translate(match.parentTypeName)),
            ),
        )
