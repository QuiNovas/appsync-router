#!/usr/bin/env python3.8
from appsync_router.resolver import router


@router.route(path="Query.GetFoo")
def get_foo(event):
    print("Called GetFoo!!!!!")
    return event
