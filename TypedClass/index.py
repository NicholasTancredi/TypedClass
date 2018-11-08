from typing import Callable, Dict, Type, Tuple, Any
from inspect import signature
import unittest


TypeDefTypeof = (Type, Tuple[Type])


class TypeDef:
    """
        TypeDef
        Used as a advanced type hint combined with TypedClass
        arguments:
            typeof: must be a "TypeDef", "type" or "tuple" of "types",
                    which is passed to "isinstance" for type validation.
            required: is the value a required attribute on the class?
            immutable: is the value static, (i.e. can't be changed)
            choices: a list of valid possible values for the value, (same as argparse)
            validate_fn: A function that takes a single argument, the value,
                        and returns a boolean indicating if the value is valid.
                        Example: os.path.isfile is a useful "validate_fn"
        example input:
            TypeDef(
                typeof=str
                required=True
                immutable=True
                choices=['a.txt', 'b.txt']
                validate_fn=os.path.isfile
            )
        NOTE: No need to use this method if you are not setting one of the optional values.
        Instead of:
            value: TypeDef(typeof=str)
        you should just use:
            value: str
        TypedClass will treat them the same.
    """
    typeof: TypeDefTypeof
    required: bool = False
    immutable: bool = False
    choices: list = None
    validate_fn: Callable = None

    def __init__(
        self,
        typeof: TypeDefTypeof,
        required: bool = False,
        immutable: bool = False,
        choices: list = None,
        validate_fn: Callable = None,
    ):
        try:
            isinstance('', typeof)
        except TypeError:
            raise TypeError("""
                TypeDef "typeof" must be a "TypeDef", "type" or "tuple" of "types",
                but a type of "{}" was provided, with the exact value of "{}"
            """.format(type(typeof), typeof))

        if not isinstance(required, bool):
            raise TypeError("""
                TypeDef "required" must be a "bool",
                but a type of "{}" was provided, with the exact value of "{}"
            """.format(type(required), required))

        if not isinstance(immutable, bool):
            raise TypeError("""
                TypeDef "immutable" must be a "bool",
                but a type of "{}" was provided, with the exact value of "{}"
            """.format(type(immutable), immutable))

        if choices is not None:
            if not isinstance(choices, list):
                raise TypeError("""
                    TypeDef "choices" must be a "list",
                    but a type of "{}" was provided, with the exact value of "{}"
                """.format(type(choices), choices))
            for choice in choices:
                if not isinstance(choice, typeof):
                    raise TypeError("""
                        TypeDef "choices" must be a "list" of valid types set by "typeof",
                        but a type of "{}" was provided, with the exact value of "{}"
                    """.format(type(choice), choice))

        if validate_fn is not None:
            if not isinstance(validate_fn, Callable):
                raise TypeError("""
                    TypeDef "validate_fn" must be "Callable" or "None",
                    but a type of "{}" was provided, with the exact value of "{}"
                """.format(type(validate_fn), validate_fn))

            validate_fn_signature = signature(validate_fn)

            arg_length = len(list(validate_fn_signature.parameters))

            if arg_length > 1:
                raise ValueError("""
                    TypeDef "validate_fn" must only have one argument;
                    but "{}" arguments were found, with the exact value of "{}"
                """.format(arg_length, list(validate_fn_signature.parameters)))

        self.typeof = typeof
        self.required = required
        self.immutable = immutable
        self.choices = choices
        self.validate_fn = validate_fn


class TypedClass:
    """
        TypedClass
        Validates type hints (i.e. __annotations__)
        @property
            attributes: Class annotated attributes as a dict.
            annotations: Safe access to __annotations__, with custom error message.
    """
    def __init__(self, **kwargs):
        self.__attributes_with_defaults_keys = []

        for key in self.annotations:
            if hasattr(self, key):
                self.__attributes_with_defaults_keys.append(key)

        for key in kwargs:
            if kwargs[key] is not None:
                setattr(self, key, kwargs[key])

        del self.__attributes_with_defaults_keys

        unset_required_props = []

        for key in self.annotations:
            annotation_value = self.annotations[key]

            if isinstance(annotation_value, TypeDef):
                if annotation_value.required and not hasattr(self, key):
                    unset_required_props.append(key)

        if unset_required_props:
            raise AttributeError(
                """
                    Missing required attributes for keys {}
                """.format(unset_required_props)
            )

    def __setattr__(self, key, value):
        if key == '_TypedClass__attributes_with_defaults_keys':
            super().__setattr__(key, value)
            return

        if key not in self.annotations:
            raise AttributeError(
                """
                    The attribute "{}" was not contained within the class annotations,
                    you may need to type hint this attribute in your class,
                    or this may be an incorrect spelling.
                    Available attributes on this class are "{}"
                """.format(key, self.annotations)
            )

        annotation_value = self.annotations[key]

        if isinstance(annotation_value, TypeDef):
            if not isinstance(value, annotation_value.typeof):
                raise TypeError("""
                    "{key}" must be a "{typeof}",
                    but a type of "{value_type}" was provided, with the exact value of "{value}"
                """.format(
                    key=key,
                    typeof=annotation_value.typeof,
                    value_type=type(value),
                    value=value))

            if annotation_value.immutable:
                if key in self.__dict__:
                    raise AttributeError("""
                        The attribute "{}" is immutable; it can't be changed.
                    """.format(key))
                # NOTE: Edge case here is that you can update an immutable
                # value if it had a default value, but only once.
                # The code below fixes this possible issue.
                elif annotation_value.immutable:
                    invalid_immutable = False

                    try:
                        getattr(self, key)
                        print(self.__attributes_with_defaults_keys)
                        print(key)
                        print(key in self.__attributes_with_defaults_keys)
                        print(hasattr(self, '_TypedClass__attributes_with_defaults_keys'))
                        if not hasattr(self, '_TypedClass__attributes_with_defaults_keys') or key not in self.__attributes_with_defaults_keys:
                            invalid_immutable = True
                            # self.__attributes_with_defaults_keys = list(
                            #     filter(lambda x: x != key, self.__attributes_with_defaults_keys)
                            # )
                    except AttributeError:
                        pass

                    if invalid_immutable:
                        raise AttributeError("""
                            The attribute "{}" is immutable; it can't be changed.
                            This attribute was initially set by a default value.
                        """.format(key))

            if annotation_value.choices is not None:
                if value not in annotation_value.choices:
                    raise TypeError("""
                        The attribute "{}" was not one of the valid TypeDef "choices".
                        A type of "{}" was provided, with the exact value of "{}".
                        The available choices are "{}"
                    """.format(key, type(value), value, annotation_value.choices))

            if annotation_value.validate_fn is not None:
                validate_fn_result = annotation_value.validate_fn(value)
                if not isinstance(validate_fn_result, bool):
                    raise TypeError("""
                        A TypeDef "validate_fn" must return a "bool", 
                        but the "validate_fn" for "{}" return a "{}"
                    """.format(key, type(validate_fn_result)))
                elif not validate_fn_result:
                    raise TypeError("""
                        The attribute "{}" failed it's TypeDef "validate_fn".
                        A type of "{}" was provided, with the exact value of "{}"
                    """.format(key, type(value), value))

        elif not isinstance(value, annotation_value):
            if isinstance(annotation_value, tuple):
                type_or_tuple_of_types = "must be one of"
            else:
                type_or_tuple_of_types = "must be a"

            raise TypeError("""
                "{key}" {type_or_tuple_of_types} "{typeof}",
                but a type of "{value_type}" was provided, with the exact value of "{value}"
            """.format(
                key=key,
                type_or_tuple_of_types=type_or_tuple_of_types,
                typeof=annotation_value,
                value_type=type(value),
                value=value))

        super().__setattr__(key, value)

    def __delattr__(self, key):
        if key in self.annotations:
            if self.annotations[key].immutable:
                raise AttributeError("""
                    The attribute "{}" is immutable; it can't be deleted.
                """.format(key))

        super().__delattr__(key)

    @property
    def attributes(self) -> Dict[str, Any]:
        result = {}
        for key in self.annotations:
            try:
                value = getattr(self, key)
                result[key] = value
            except AttributeError:
                pass
        return result

    @property
    def annotations(self) -> dict:
        """
            NOTE: __annotations__ is not on the class if the child class doesn't use any
        """
        try:
            return getattr(self, '__annotations__')
        except AttributeError:
            raise AttributeError(
                """
                    While using "TypedClass" you must provide annotations on your class.
                    (i.e. type hints)
                """
            )


class TypedClassStrict(TypedClass):
    def __init__(self, **kwargs):
        for key in self.annotations:
            annotation_value = self.annotations[key]
            if isinstance(annotation_value, TypeDef):
                if not annotation_value.required:
                    required = False
                else:
                    required = True

                if not annotation_value.immutable:
                    immutable = False
                else:
                    immutable = True

                self.annotations[key] = TypeDef(
                    typeof=annotation_value.typeof,
                    required=required,
                    immutable=immutable,
                    choices=annotation_value.choices,
                    validate_fn=annotation_value.validate_fn
                )
            else:
                self.annotations[key] = TypeDef(
                    typeof=annotation_value,
                    required=True,
                    immutable=True
                )
        super().__init__(**kwargs)


TypeExampleAllOptions = (int, str, Callable, TypeDef, TypedClass)


class ExampleTypedClass(TypedClassStrict):
    simple_type_hint: int

    type_hint: TypeDef(
        typeof=int,
        required=True,
        immutable=True
    )

    simple_type_hint_with_default: float = 1.01

    type_hint_with_default: TypeDef(
        typeof=int,
        required=True,
        immutable=True
    ) = 22

    all_options: TypeDef(
        typeof=TypeExampleAllOptions,
        required=True,
        immutable=True,
        choices=[21, 22, 23],
        validate_fn=lambda x: x > 20
    ) = 23

    def __init__(
            self,
            simple_type_hint: int,
            type_hint: int,
            simple_type_hint_with_default: float = 1.01,
            type_hint_with_default: int = 22,
            all_options: TypeExampleAllOptions = 23,
    ):
        super().__init__(
            simple_type_hint=simple_type_hint,
            type_hint=type_hint,
            simple_type_hint_with_default=simple_type_hint_with_default,
            type_hint_with_default=type_hint_with_default,
            all_options=all_options
        )


class TestTypedClass(unittest.TestCase):
    """
        class TestTypedClass
    """
    def test(self):
        """
            def test
        """
        example = ExampleTypedClass(
            simple_type_hint=23,
            type_hint=23,
            simple_type_hint_with_default=1.02,
            type_hint_with_default=24,
            all_options=23
        )
        self.assertEqual(example.type_hint, 23)
        self.assertEqual(example.attributes['simple_type_hint'], 23)


if __name__ == '__main__':
    unittest.main()


def methodName(variableName: str) -> str:
    return variableName

