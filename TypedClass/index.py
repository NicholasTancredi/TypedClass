from typing import Callable
from inspect import signature

class TypeDef:
    def __init__(
        self,
        typeof: type,
        required: bool = False,
        immutable: bool = False,
        choices: list = None,
        validate_fn: Callable = None,
    ):
        try:
            isinstance('', typeof)
        except:
            raise TypeError("""
                "typeof" must be a "TypeDef", "type" or "tuple" of "types",
                but a type of "{}" was provided, with the exact value of "{}"
            """.format(type(typeof), typeof))

        if not isinstance(required, bool):
            raise TypeError("""
                "required" must be a "bool",
                but a type of "{}" was provided, with the exact value of "{}"
            """.format(type(required), required))

        if not isinstance(immutable, bool):
            raise TypeError("""
                "immutable" must be a "bool",
                but a type of "{}" was provided, with the exact value of "{}"
            """.format(type(immutable), immutable))

        if validate_fn is not None:
            if not isinstance(choices, list):
                raise TypeError("""
                    "choices" must be a "list",
                    but a type of "{}" was provided, with the exact value of "{}"
                """.format(type(choices), choices))

        if validate_fn is not None:
            if not isinstance(validate_fn, Callable):
                raise TypeError("""
                    "validate_fn" must be "Callable" or "None",
                    but a type of "{}" was provided, with the exact value of "{}"
                """.format(type(validate_fn), validate_fn))

            validate_fn_signature = signature(validate_fn)

            arg_length = len(list(validate_fn_signature.parameters))

            if arg_length > 1:
                raise ValueError("""
                    "validate_fn" must only have one argument;
                    but "{}" arguments were found, with the exact value of "{}"
                """.format(arg_length, list(validate_fn_signature.parameters)))

        self.typeof = typeof
        self.required = required
        self.immutable = immutable
        self.choices = choices
        self.validate_fn = validate_fn

def get_annotations(_self) -> dict:
    # NOTE: __annotations__ is not on the class if the child class doesn't use any
    try:
        return getattr(_self, '__annotations__')
    except:
        raise AttributeError(
            """
                While using "TypedClass" you must provide annotations on your class.
                (i.e. type hints)
            """
        )

class TypedClass:
    def __init__(self, **props):
        annotations = get_annotations(self)

        attributes_with_defaults_keys = []
        for key in annotations:
            try:
                getattr(self, key)
                attributes_with_defaults_keys.append(key)
            except:
                pass

        self.__attributes_with_defaults_keys = attributes_with_defaults_keys

        for key in props:
            if key == '_TypedClass__attributes_with_defaults_keys':
                raise AttributeError(
                    """
                        TypedClass uses the key "_TypedClass__attributes_with_defaults_keys",
                        please use something else.
                    """
                )
            setattr(self, key, props[key])

        del self.__attributes_with_defaults_keys

        unset_required_props = []

        for key in annotations: 
            annotation_value = annotations[key]

        if isinstance(annotation_value, TypeDef):
            if annotation_value.required:
                try:
                    getattr(self, key)
                except:
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

        annotations = get_annotations(self)

        if key not in annotations:
            raise AttributeError(
                """
                    The attribute "{}" was not contained within the class annotations,
                    you may need to type hint this attribute in your class, or this may be an incorrect spelling. 
                    Available attributes on this class are "{}"
                """.format(key, annotations)
            )

        annotation_value = annotations[key]

        if isinstance(annotation_value, TypeDef):
            if not isinstance(value, annotation_value.typeof):
                raise TypeError("""
                    "{key}" must be a "{typeof}",
                    but a type of "{value_type}" was provided, with the exact value of "{value}"
                """.format(key=key, typeof=annotation_value.typeof, value_type=type(value), value=value))

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
                        if key not in self.__attributes_with_defaults_keys:
                          invalid_immutable = True
                    except:
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
        annotations = get_annotations(self)

        if key in annotations:
            if annotations[key].immutable:
                raise AttributeError("""
                    The attribute "{}" is immutable; it can't be deleted.
                """.format(key))

        super().__delattr__(key)

    def get_attributes(self) -> dict:
        result = {}
        annotations = get_annotations(self)
        for key in annotations:
            try:
                value = getattr(self, key)
                result[key] = value
            except:
                pass
        return result

class Test(TypedClass):
    simple_type_hint: int
    simple_type_hint_with_default: float = 1.01

    type_hint: TypeDef(
        typeof=(int, float),
        required=True,
        immutable=True
    )

    type_hint_with_default: TypeDef(
        typeof=int,
        required=True,
        immutable=True
    ) = 22

    the_works: TypeDef(
        typeof=(int, str, Callable, TypeDef, TypedClass),
        required=True,
        immutable=True,
        choices=[21, 22, 23],
        validate_fn=lambda x: x > 20
    ) = 22

    def __init__(self, **props):
        TypedClass.__init__(self, **props)
        print('extended __init__ while keeping parent class __init__ method')
