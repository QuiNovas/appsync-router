from __future__ import annotations

from typing import Any, Dict, List, TypedDict, Union


class Context(TypedDict, total=False):
    arguments: Dict[str, Any]
    identity: Union[CognitoUserPoolIdentity, IamIdentity, LambdaIdentity]
    info: Info
    prev: Prev
    request: Request
    source: Dict[str, Any]
    stash: Dict[Any, Any]


class Prev(TypedDict):
    result: Dict[str, Any]


class Request(TypedDict):
    headers: Dict[str, str]


class Info(TypedDict, total=False):
    fieldName: str
    parentTypeName: str
    selectionSetGraphQL: str
    selectionSetList: List[str]
    variables: Dict[str, Any]


LambdaIdentity = Dict[Any, Any]


class IamIdentity(TypedDict, total=False):
    accountId: str
    cognitoIdentityAuthProvider: str
    cognitoIdentityAuthType: str
    cognitoIdentityId: str
    cognitoIdentityPoolId: str
    sourceIp: List[str]
    username: str
    userArn: str


class CognitoUserPoolIdentity(TypedDict):
    claims: Dict[str, Any]
    defaultAuthStrategy: str
    issuer: str
    sourceIp: List[str]
    sub: str
    username: str
