from __future__ import annotations

from typing import Any, TypedDict, Union


class Context(TypedDict, total=False):
    arguments: dict[str, Any]
    identity: Union[CognitoUserPoolIdentity, IamIdentity, LambdaIdentity]
    info: Info
    prev: Prev
    request: Request
    source: dict[str, Any]
    stash: dict[Any, Any]


class Prev(TypedDict):
    result: dict[str, Any]


class Request(TypedDict):
    headers: dict[str, str]


class Info(TypedDict, total=False):
    fieldName: str
    parentTypeName: str
    selectionSetGraphQL: str
    selectionSetList: list[str]
    variables: dict[str, Any]


LambdaIdentity = dict[Any, Any]


class IamIdentity(TypedDict, total=False):
    accountId: str
    cognitoIdentityAuthProvider: str
    cognitoIdentityAuthType: str
    cognitoIdentityId: str
    cognitoIdentityPoolId: str
    sourceIp: list[str]
    username: str
    userArn: str


class CognitoUserPoolIdentity(TypedDict):
    claims: dict[str, Any]
    defaultAuthStrategy: str
    issuer: str
    sourceIp: list[str]
    sub: str
    username: str
