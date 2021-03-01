.. appsync-router documentation master file, created by
   sphinx-quickstart on Mon Mar  1 14:28:23 2021.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to appsync-router's documentation!
==========================================

.. toctree::
   :maxdepth: 2

Introduction
============
This module provides a framework for creating a backend to resolve Appsync calls in AWS Lambda. It provides the following features:
- Path based routing based on the Appsync parent type and field
- Regex based path matching
- Path matching using Unix-like glob patters
- Resolving by "First match wins" or returning the results of multiple matching routes
- Any callable that accepts an AWS Lambda *event* dict can be used to handle a route
- Tools for generating a project skeleton and testing resolvers


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
   router = Route()

   @router.route(path="Query.GetFoo")
   def get_foo(event):
      print("Hello Foo!!!)
      return event


The second way is to manually add a route.

..code-block:: python

   from appsync_router import Route, NamedRoute

   def get_foo(event):
      print("Hello Foo!!!)
      return event

   router = Route()
   my_route = NamedRoute("Query.GetFoo", get_foo)
   router.add_route(my_route)



Classes
=======

The Router class
----------------
.. autoclass:: appsync_router.Router
   :members:

Route types
-----------
.. autoclass:: appsync_router.Item
   :members:

.. autoclass:: appsync_router.NamedRoute
   :members:

.. autoclass:: appsync_router.MatchedRoute
   :members:

.. autoclass:: appsync_router.GlobbedRoute
   :members:

.. autoclass:: appsync_router.DefaultRoute
   :members:

Responses
---------
.. autoclass:: appsync_router.Response
   :members:

Exceptions
----------
.. automodule:: appsync_router.exceptions
   :members:

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

