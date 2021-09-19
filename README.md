# appsync-router

> **WARNING - Version 4.0.0 is a breaking change from version 3.x.x. Please review the documentation before upgrading**

A micro-library that allows for the registration of functions corresponding to
AWS AppSync routes. This allows for cleanly creating a single AWS Lambda datasource
without large numbers of conditionals to evaluate the called route.

## Installation
```bash
pip install appsync-router
```

## Basic Usage
```python
from appsync_router import discrete_route, route_event
# Context is a TypedDict that makes access to
# the items passed to your Lambda function simpler
from appsync_router.context import Context

# Here we are telling the router that when the field "getItems"
# is called on the type "Query", call the function "get_items"
@discrete_route("Query", "getItems")
def get_items(context: Context) -> list:
    return [1, 2, 3, 4]

def function_handler(event, context):
    # simply route the event and return the results 
    return route_event(event)
```

> NOTE - `appsync-router` is designed to be used as a Direct Invocation AWS AppSync
datasource. If you put a request VTL template in front of it, you must pass in the WHOLE
$ctx/$context object.

## Route Types

Each route type has an overloaded signature allowing for simple declaration.

- `discrete_route` - This discretely routes to a named type and field
- `multi_route` - This routes to a set of named type/field combinations
- `pattern_route` - This routes to types/fields that match the type and field regex patterns provided
- `glob_route` - This routes to the types/fields that match the type and field glob patterns provided

## Routing Events
As seen in the example above, the simplest form of event routing is to call `route_event` with only the event argument. This will do the following:

1. Determine the route for the event
    1. If no route is found, raise `NoRouteFoundException`
    2. If more than one route is found, use the first route found
2. Route the event if it is a single context, or map the event to the route if it is multiple contexts

Many times this will be sufficient. However, this behavior can be modified:
- Passing a `default_route` of type `Route` to the `route_event` method will call your `default_route` if no route is found
- Passing `short_circuit=False` to the `route_event` method will cause a `MultipleRoutesFoundException` to be raised in the case of multiple matched routes.
- Passing an `executor` of type `concurrent.futures.Executor` to the `route_event` method will cause all batch invocations (where the `event` has a list of contexts) to be executed using your executor.

## Extensibility
You may extend the `appsync_router` with your own route types. Any routes that you create must extend from the `appsync_router.routes.Route` class.
