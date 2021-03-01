#!/usr/bin/env python3.8
from appsync_router.resolver import router


@router.route(path="Reports.locations")
def get_foo(event):
    print("Explicit Route")


event = {
    "info": {
        "parentTypeName": "Reports",
        "fieldName": "locations",
        "arguments": {},
        "source": {}
    }
}
