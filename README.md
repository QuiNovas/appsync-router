# appsync-tools

##Provides helpful tools for parsing database responses and handling routes inside of Lambda for AWS Appsync.


## DB response parsing
Aurora results are returned as a list of dictionaries with the column names being the key.
Nulls (returned by Aurora as isNull) are returned as None types. Any value that can be parsed as json is cast from a string to a list/dictionary.
Responses are returned formated as:

```json

  [
    {"columnOneName": "value", "columnTwoName": "value"},
    {"columnOneName": "value", "columnTwoName": "value"}
  ]
```

Where each item in the top level array is a separate row.

Dynamodb results are returned as either a dictionary (for get_item operations) or a list of dictionaries (query).


Pretty parsing Aurora records
-----------------------------

pretty_parse_aurora(records, type_attribute=None) -> list

**Arguments:**
- records -- The records from the API query (execute_statement()["records"])

**Keyword Args:**
- type_attribute -- If used will pass results to typify(results, type_attribute=type_attribute) before returning


```python

  from appsync_tools import pretty_parse_aurora

  response = client.execute_statement(
      secretArn=environ["PG_SECRET"],
      database=environ["DB_NAME"],
      parameters=parameters,
      resourceArn=environ["DB_ARN"],
      includeResultMetadata=True,
      sql=sql
  )
  print(pretty_parse_aurora(response))
```


Parsing Dynamodb records
----------------------------

pretty_parse_dynamo(records, type_attribute=None) -> list | dict

**Arguments:**
- records -- The Item(s) from a call to query, get_item

**Keyword Args:**
- type_attribute -- If used will pass results to typify(results, type_attribute=type_attribute) before returning

```python

  from appsync_tools import pretty_parse_dynamo

  response = client.get_item(
    Key={"pk": "foo", "sk": "bar"}
  )
  print(response.get("Item"))
```


Adding __typename to all records based on an attribute
------------------------------------------------------

typify(records, type_attribute="type") -> list | dict
**Arguments:**
- records -- The Item(s) from a call to query, get_item

**Keyword Args:**
- type_attribute -- Attribute name that contains the __typename value

Example
----------------------------

```python

  from appsync_tools import typify

  response = client.get_item(
    Key={"pk": "foo", "sk": "BarType"}
  )

  print(typify(response.get("Item"), type_attribute="sk"))
```


## Appsync resolver function routing
### Creating a route
appsync_tools.router is an instance of appsync_tools.router.Router. The router object can be used to specify that a function is used for a
specific Appsync type by decoration the function with the router.route() method. The decorated function should accept the Lambda event as
its only argument.

**@router.route(route: str|list[str]|re.Pattern) -> function**
**keyword Args:**
- route -- The route(s) that this function applies to. "route" is expressed as <parent type>.<type>. For example, using this schema:

```
type Foo {
  bar: str!
}

Query {
  GetFoo: Foo
}
```

the route passed to the decorator to handle GetFoo would be "Query.GetFoo". route can be either a single route or a list of routes.

Example
----------------------------
```python
  from appsync_tools import router


  def handler(event, _):
    router.handle_route(event)


  @router.route(route="Query.GetFoo)
  def get_foo(event):
    print("Foo")


  event = {
    "info": {"parentType": "Query", "field": "GetFoo"}
  }


  handler(event, None)

  # Will print: 'Foo'

```

### Regular expression matching
You can provide regular expression matching for routes using the matched_route decorator. **router.matched_routes** are looked up after checking for an explicit match
in **router.routes**. If not explicit matches exist then the Appsync call is tested against each expression in **router.matched_routes** until either a match is made
or the end is reached. In the case of a match being found it is the first match in **router.matched_routes** that is used. The expression passed as **regex** can be either
of type str(), which router will attept to compile into a Pattern, or a Pattern of type re.Pattern that has already been compiled using re.compile.

**@router.matched_route(regex: str|re.Pattern) -> function**
**keyword Args:**
- regex: Either a string that can be compiled into a regex using re.Compile or an instance of re.Pattern that has already been compiled.

Example
----------------------------
```python
  from appsync_tools import router


  def handler(event, _):
    router.handle_route(event)


  @router.matched_route(regex="^Query\.Search.*")
  def search_foo(event):
    print("Matched!!!!!)


  event = {
    "info": {"parentType": "Query", "field": "SearchFoo"}
  }


  handler(event, None)

  # Will print: 'Matched!!!!!'

```

### Glob style matching
The **router.globbed_route** decorator provides Unix file glob style matchinf for routes. **router.globbed_routes** are looked up after checking for an explicit match
in **router.routes**, and a regex match in **router.matched_routes**. The Appsync call is tested against each expression in **router.globbed_routes** using fnmatch.filter
until either a match is made or the end is reached. In the case of a match being found it is the first match in **router.globbed_routes** that is used.

**@router.globbed_route(glob: str) -> function**
**keyword Args:**
- glob: Either a string that can be compiled into a regex using re.Compile or an instance of re.Pattern that has already been compiled.

Example
----------------------------
```python
  from appsync_tools import router


  def handler(event, _):
    router.handle_route(event)


  @globbed.matched_route(regex="*.Search")
  def search_foo(event):
    print("Globbed!!!!!)


  event = {
    "info": {"parentType": "Query", "field": "SearchFoo"}
  }


  handler(event, None)

  # Will print: 'Globbed!!!!!'

```


### Creating a default route
Decorating a function with **@default_route** will make it the default function to call if there are no matching routes. It takes no direct arguments

Example
----------------------------
```python
  from appsync_tools import router


  def handler(event, _):
      router.handle_route(event)


  @router.route(route="Query.GetFoo")
  def get_foo(event):
      print("bar")


  @router.default_route
  def default(event):
      print("hey, I'm the default route")


  event = {
      "info": {
          "parentType": "No",
          "field": "Route",
      }
  }

  handler(event)

  # Will print: "hey, I'm the default route"
```

### Routes are resolved in the order of:
- Routes explicitely defined using router.route
- Routes matched using router.matched_route
- Routes matched using router.globbed_route
- Default route

**If no matching route is found then appsync_tools.exceptions.NonExistentRouteException will be raised**