#!/usr/bin/env python3.8
from appsync_router.resolver import router


@router.default
def default_handler(event):
    print("hey, I'm the default route")


@router.matched_route(regex="Report.*", priority=5)
def wildcard_route(event):
    print("I am a regex matched route")


@router.globbed_route(glob="Report*", priority=3)
def globbed_route(event):
    print("I am a glob matched route")


event = {
    "info": {
        "parentTypeName": "Reports",
        "fieldName": "locations",
        "arguments": {},
        "source": {}
    }
}
