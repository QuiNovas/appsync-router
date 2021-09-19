import re
from typing import NamedTuple


class DiscreteMatch(NamedTuple):
    parentTypeName: str
    fieldName: str

    def __str__(self) -> str:
        return f'DiscreteMatch(parentTypeName="{self.parentTypeName}", fieldName="{self.fieldName}")'


class GlobMatch(NamedTuple):
    parentTypeName: str
    fieldName: str

    def __str__(self) -> str:
        return f'GlobMatch(parentTypeName="{self.parentTypeName}", fieldName="{self.fieldName}")'


class PatternMatch(NamedTuple):
    parentTypeName: re.Pattern
    fieldName: re.Pattern

    def __str__(self) -> str:
        return f'PatternMatch(parentTypeName="{self.parentTypeName.pattern}", fieldName="{self.fieldName.pattern}")'
