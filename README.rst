Introduction
============

This module provides a framework for creating a backend to resolve Appsync calls in AWS Lambda.
-----------------------------------------------------------------------------------------------

Full documentation is available `HERE <https://quinovas.github.io/appsync-router>`_

Features:
---------

- Path based routing based on the Appsync parent type and field
- Regex based path matching
- Path matching using Unix-like glob patters
- Resolving by "First match wins" or returning the results of multiple matching routes
- Any callable can be used to handle a route
- Tools for generating a project skeleton and testing resolvers
- The ability to chain resolvers by passing the result of one as the input to the next


How it works
------------

Routes are resolved by matching a *path* to a callable (function, lambda, class, etc). Paths are represented as:

.. code-block:: python

   path = f'{event["info"]["parentTypeName"]}.{event["info"]["fieldName"]}'


with *event* being the event argument passed to Lambda. To create a function that will resolve to a specific path we can
decorate it, creating a Route. Here are the available types of Routes:

- NamedRoute: Matches the exact path. There can only be one NamedRoute in a Router per specific path
- MatchedRoute: Uses a regular expression to match a path. The expression provided can be either a string or an instance of re.Pattern
- GlobbedRoute: Matches routes using Unix-like file globbing patters
- DefaultRoute: There can only be one DefaultRoute in a router. Attempting to register a second will raise an exception


Creating routes
---------------
There are two ways to build a Router. The easiest is to use decorators. Here is an example of creating a NamedRoute using a decorator.

.. code-block:: python

   from appsync_router import Route
   router = Router()

   @router.route(path="Query.GetFoo")
   def get_foo():
      print("Hello Foo!!!)
      return event


The second way is to manually add a route.

.. code-block:: python

   from appsync_router import Router, NamedRoute

   def get_foo(foo, bar, baz=True):
      print("Hello Foo!!!)
      return router.event

   router = Router()
   my_route = NamedRoute("Query.GetFoo", get_foo)
   router.add_route(my_route)


Function signatures
-------------------
You may have noticed that when using the decorator our function signature took no arguments. This is because we are accessing the event via ``router.event``.
You can define your functions to take any number of arguments as long as those arguments allow for their value to be ``None``. When a route is handled by
``resolve()`` or ``resolve_all()`` then when the function is called the arguments will be handled as follows:

- All positional arguments will be passed ``None`` as their value the router
- No keyword args will be passed

This allows for reusing functions so you can register them as a route or call them directly from somewhere else using whatever signature you prefer.


Multiple Route matching
-----------------------
Calling ``Router.resolve_all()`` will call every route that matches the event's path. Results from each function that is called is appended to
``Router().prev`` so you can access the results from any route that is called in subsequent routes.


The event property
------------------
The event is passed to the Router() object by a call to either ``Router().init(event)`` or by passing the event as an argument to ``Router().resolve()``
or ``Router().resolve_all()``. The Router().event is immutable once set, which guarantees that what was originally passed stays intact. You can use the
``Router().stash`` property to pass arbitrary data between function calls if necessary. Once ``Router().event`` is set the event is accessible from anywhere
that has access to the ``Router()`` object.


Stashing data
-------------
You can store arbitrary data as in ``Router().stash``. The stash can be treated as a ``dict`` and can be accessed anywhere that the ``Router()`` object is accessible.


Resolver framework
==================

The module installs a console script into ``$PATH`` that can be used to:

- Create a resolver based app skeleton
- Generate a Lambda function using lambda_setup_tools package (must be installed separately)
- Test routes/Lambda function by passing an event or event file
- Generate a new ``resolver``


resolvers
---------
A resolver package is a module that is placed in your script's working directory. The module consists of ``resolvers``, which are your scripts that contain
decorated functions to create routes and a ``Router()`` object (named "router") to be imported by your Lambda function. When using the resolver framework your main script
imports ``resolvers.router``, which will be a local import of the resolvers directory in the main script's directory. Here is an example of the directory structure:
::

   my_lambda.py
   /resolvers
      __init__.py
      config.json
      first_resolver.py
      another_resolver.py


Example of first_resolver.py:

.. code-block:: python

   from resolvers import router

   @router.route("Query.GetFoo")
   def get_foo():
      print("Here is Foo!!!!!")



Your lambda would then import ``resolvers.router``. Here is an example lambda that uses the above resolver package:

.. code-block:: python

   from resolvers import router

   event = {
      "info": {"parentTypeName": "Query", "fieldName": "GetFoo"}
   }

   def handler(event, ctx):
      router.resolve(event)

   # Prints "Here is Foo!!!!!"

Here is what happens in the example:

- first_resolver.py imports the router object from __init__.py using ``from resolvers import router``
- All routes in first_resolver.py are added to the ``route`` object
- If there are any other files in ``resolvers`` their routes are also added to a new ``route`` object
- my_lambda.py imports the ``resolvers.route`` object, which contains a new route object containing all routes from resolvers merged together
- The route object imported into my_lambda.py takes its arguments from resolvers/config.json
- Executing lambda.handler() in my_lambda.py gets the routes registered from the resolvers package and resolves the route, calling ``get_foo()``


Creating a lambda that uses the resolvers framework
---------------------------------------------------
First create a skeleton using the console script:

::

   >appsync-router make-app --app-dir .

      App created. You can test your app by running:
         appsync-router execute --event-file example.json --pprint
      Or add a new resolver with:
         appsync-router add-resolver --resolver-name <new name>


Now add a resolver:

::

   >appsync-router add-resolver --resolver-name foo
   >rm -f resolvers/example.py #remove the example
   >ls resolvers
   __init__.py foo.py


Edit resolvers/foo.py to contain the following:

.. code-block:: python

   from resolvers import router


   @router.route(path="Query.GetFoo")
   def get_foo():
      print("Called GetFoo!!!!!")
      return router.event


Test your resolver using the script:

::

   >appsync-router execute-lambda --event '{"info": {"parentTypeName": "Query", "fieldName": "GetFoo"}}'
   Hello Foo!!!!!
   [
      {
         "route": {
               "path": "Query.GetFoo",
               "callable": "get_foo",
               "type": "named_route",
               "resolver": "resolvers.foo"
         },
         "value": {
               "info": {
                  "parentTypeName": "Query",
                  "fieldName": "GetFoo"
               }
         }
      }
   ]


To test from your own script, create a file that contains the following:

.. code-block:: python

   from resolvers import router

   def handler(event, ctx):
      res = router.resolve(event)
      print(res.values)


   event = {
      "info": {"parentTypeName": "Query", "fieldName": "GetFoo"}
   }

   handler(event, None)


And execute with:

::

   > python3.8 my_lambda.py
   Hello Foo!!!!!
   [{'info': {'parentTypeName': 'Query', 'fieldName': 'GetFoo'}}]


Add a resolvers package without creating a Lambda package
---------------------------------------------------------

Passing ``--no-lambda`` to ``appsync-router make-app`` will create a resolvers package in the current working directory without creating the full Lambda skeleton

You can also execute a route directly by calling ``appsync-router execute-resolver --event``. This passes the event directly to the route's callable instead of the handler of a Lambda

