from typing import Callable

import keras


def find_distribution(distribution: str | Callable, **kwargs):
    #TODO -> return type
    match distribution:
        case str() as name:
            match name.lower():
                case "normal":
                    from bayesflow.experimental.distributions import DiagonalNormal
                    distribution = DiagonalNormal(**kwargs)
                case other:
                    raise NotImplementedError(f"Unsupported distribution name: '{other}'.")
        case Callable() as constructor:
            distribution = constructor(**kwargs)
        case other:
            raise TypeError(f"Cannot infer distribution from {other!r}.")

    return distribution


def find_network(network: str | keras.Layer | Callable, **kwargs) -> keras.Layer:
    match network:
        case str() as name:
            match name.lower():
                case "resnet":
                    from bayesflow.experimental.networks import ResNet
                    network = ResNet(**kwargs)
                case other:
                    raise NotImplementedError(f"Unsupported network name: '{other}'.")
        case keras.Layer() as network:
            pass
        case Callable() as constructor:
            network = constructor(**kwargs)
        case other:
            raise TypeError(f"Cannot infer network from {other!r}.")

    return network