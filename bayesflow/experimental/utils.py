
import keras

from bayesflow.experimental.types import Tensor


def nested_getitem(data: dict, item: int) -> dict:
    """ Get the item-th element from a nested dictionary """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = nested_getitem(value, item)
        else:
            result[key] = value[item]
    return result


def nested_merge(a: dict, b: dict) -> dict:
    """ Merge a nested dictionary A into another nested dictionary B """
    for key, value in a.items():
        if isinstance(value, dict):
            b[key] = nested_merge(value, b.get(key, {}))
        else:
            b[key] = value
    return b


def apply_nested(fn: callable, data: dict) -> dict:
    """ Apply a function to all non-dictionaries in a nested dictionary """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = apply_nested(fn, value)
        else:
            # TODO: consuming version? this is not memory efficient
            result[key] = fn(value)

    return result


def expand_left(tensor: Tensor, n: int) -> Tensor:
    """ Expand a tensor to the left n times """
    idx = [None] * n + [slice(None)] * keras.ops.ndim(tensor)
    return tensor[idx]


def expand_right(tensor: Tensor, n: int) -> Tensor:
    """ Expand a tensor to the right n times """
    idx = [slice(None)] * keras.ops.ndim(tensor) + [None] * n
    return tensor[idx]