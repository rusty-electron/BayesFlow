import keras
from keras.saving import register_keras_serializable

from bayesflow.types import Tensor
from bayesflow.utils import keras_kwargs


@register_keras_serializable(package="bayesflow.networks")
class ResNet(keras.Layer):
    """Implements a super-simple ResNet"""

    def __init__(self, depth: int = 6, width: int = 256, activation: str = "gelu", **kwargs):
        super().__init__(**keras_kwargs(kwargs))

        self.input_layer = keras.layers.Dense(width)
        self.output_layer = keras.layers.Dense(width)
        self.hidden_layers = [keras.layers.Dense(width, activation) for _ in range(depth)]

    def build(self, input_shape):
        self.input_layer.build(input_shape)
        input_shape = self.input_layer.compute_output_shape(input_shape)
        for layer in self.hidden_layers:
            layer.build(input_shape)
            input_shape = layer.compute_output_shape(input_shape)

        self.output_layer.build(input_shape)

    def compute_output_shape(self, input_shape):
        input_shape = self.input_layer.compute_output_shape(input_shape)
        for layer in self.hidden_layers:
            input_shape = layer.compute_output_shape(input_shape)

        return self.output_layer.compute_output_shape(input_shape)

    def call(self, x: Tensor, **kwargs) -> Tensor:
        x = self.input_layer(x)
        for layer in self.hidden_layers:
            x = x + layer(x)

        x = x + self.output_layer(x)

        return x
