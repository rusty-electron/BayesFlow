import keras

from bayesflow.types import Shape, Tensor
from bayesflow.utils import concatenate_dicts


class Simulator:
    def sample(self, batch_shape: Shape, *, numpy: bool = False, **kwargs) -> dict[str, Tensor]:
        raise NotImplementedError

    def rejection_sample(
        self, batch_shape: Shape, condition: callable, *, axis: int = 0, numpy: bool = False, **kwargs
    ) -> dict[str, Tensor]:
        result = {}

        while not result or keras.ops.shape(next(iter(result.values())))[axis] < batch_shape[axis]:
            samples = self.sample(batch_shape, **kwargs)
            accept_mask = condition(samples)
            accept_mask = keras.ops.convert_to_tensor(accept_mask, dtype="bool")

            if not keras.ops.any(accept_mask):
                continue

            (accept_indices,) = keras.ops.nonzero(accept_mask)

            samples = {key: keras.ops.take(value, accept_indices, axis=axis) for key, value in samples.items()}

            if not result:
                result = samples
            else:
                result = concatenate_dicts([result, samples], axis=axis)

        if numpy:
            result = {key: keras.ops.convert_to_numpy(value) for key, value in result.items()}

        return result
