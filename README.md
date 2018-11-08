# TypedClass
A python class made for extended other classes giving them type checking on annotated attributes and other nice things like required attributes, immutable attributes, validation functions for attributes, choices for attributes.

# Example Usage
## TypedClass
```python
from TypedClass import TypedClass, TypeDef

class ExampleTypedClass(TypedClass):
    simple: int

    using_type_def: TypeDef(typeof=int)

    simple_with_default: float = 1.01

    type_hint_with_default: TypeDef(
        typeof=int
    ) = 22

    all_options: TypeDef(
        typeof=int,
        required=True,
        immutable=True,
        choices=[21, 22, 23],
        validate_fn=lambda x: x > 20
    ) = 23

    def __init__(
            self,
            simple: int,
            using_type_def: int,
            simple_with_default: float = 1.01,
            type_hint_with_default: int = 22,
            all_options: int = 23,
    ):
        super().__init__(
            simple=simple,
            using_type_def=using_type_def,
            simple_with_default=simple_with_default,
            type_hint_with_default=type_hint_with_default,
            all_options=all_options
        )

```

## TypedClassStrict
Same as above, only everything is set to required and immutable by default.

## TypedClassJson
```python
from TypedClass import TypedClassJson

class ExampleJSONValidationUsageObj(TypedClassJson):
    name: str
    value: str
    valid: bool

class ExampleJSONValidationUsageWithHelperClass(TypedClassJson):
    _id: int
    sender: str
    kind: str
    nested_obj: ExampleJSONValidationUsageObj
    nested_obj_with_help: ExampleJSONValidationUsageObj


example_json = {
    '_id': 1,
    'sender': 'nic',
    'kind': 'message',
    'nested_obj': {
        'name': 'nested_obj',
        'value': 'cool',
        'valid': True
    },
    'nested_obj_with_help': {
        'name': 'nested_obj_with_help',
        'value': 'very cool',
        'valid': True
    }
}

# ...

import unittest

json_output_example = ExampleJSONValidationUsageWithHelperClass(example_json)

tc = unittest.TestCase('__init__')

tc.assertEqual(example_json, json_output_example.dict)
```