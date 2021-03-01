from appsync_router.resolver import router


@router.route(path="GetFoo")
def get_foo(event):
    return event
