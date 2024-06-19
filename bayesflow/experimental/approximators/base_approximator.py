
import keras
import warnings

from bayesflow.experimental.configurators import BaseConfigurator
from bayesflow.experimental.networks import InferenceNetwork, SummaryNetwork
from bayesflow.experimental.types import Shape, Tensor


class BaseApproximator(keras.Model):
    # TODO: why does this work without the register serializable decorator?
    def __init__(self, inference_network: InferenceNetwork, summary_network: SummaryNetwork, configurator: BaseConfigurator, **kwargs):
        super().__init__(**kwargs)
        self.inference_network = inference_network
        self.summary_network = summary_network
        self.configurator = configurator

    # noinspect PyMethodOverriding
    def build(self, data_shapes: dict[str, Shape]):
        data = {name: keras.ops.zeros(shape) for name, shape in data_shapes.items()}
        self.build_from_data(data)

    def build_from_data(self, data: dict[str, Tensor]):
        self.compute_metrics(data, stage="training")
        self.built = True

    def train_step(self, data: dict[str, Tensor]) -> dict[str, Tensor]:
        # we cannot provide a backend-agnostic implementation due to reliance on autograd
        raise NotImplementedError

    def test_step(self, data: dict[str, Tensor]) -> dict[str, Tensor]:
        metrics = self.compute_metrics(data, stage="validation")
        self._loss_tracker.update_state(metrics["loss"])
        return metrics

    def evaluate(self, *args, **kwargs):
        val_logs = super().evaluate(*args, **kwargs)

        if val_logs is None:
            # https://github.com/keras-team/keras/issues/19835
            warnings.warn(f"Found no validation logs due to a bug in keras. "
                          f"Applying workaround, but incorrect loss values may be logged. "
                          f"If possible, increase the size of your dataset, "
                          f"or lower the number of validation steps used.")

            val_logs = {}

        return val_logs

    # noinspection PyMethodOverriding
    def compute_metrics(self, data: dict[str, Tensor], stage: str = "training") -> dict[str, Tensor]:
        # compiled modes do not allow in-place operations on the data object
        # we perform a shallow copy here, which is cheap
        data = data.copy()

        if self.summary_network is None:
            data["inference_variables"] = self.configurator.configure_inference_variables(data)
            data["inference_conditions"] = self.configurator.configure_inference_conditions(data)
            return self.inference_network.compute_metrics(data, stage=stage)

        data["summary_variables"] = self.configurator.configure_summary_variables(data)
        data["summary_conditions"] = self.configurator.configure_summary_conditions(data)

        summary_metrics = self.summary_network.compute_metrics(data, stage=stage)

        data["summary_outputs"] = summary_metrics.pop("outputs")

        data["inference_variables"] = self.configurator.configure_inference_variables(data)
        data["inference_conditions"] = self.configurator.configure_inference_conditions(data)

        inference_metrics = self.inference_network.compute_metrics(data, stage=stage)

        metrics = {"loss": summary_metrics["loss"] + inference_metrics["loss"]}

        summary_metrics = {f"summary/{key}": val for key, val in summary_metrics.items()}
        inference_metrics = {f"inference/{key}": val for key, val in inference_metrics.items()}

        return metrics | summary_metrics | inference_metrics

    def compute_loss(self, *args, **kwargs):
        raise RuntimeError(f"Use compute_metrics()['loss'] instead.")

    def fit(self, *args, **kwargs):
        if not self.built:
            try:
                dataset = kwargs.get("x") or args[0]
                self.build_from_data(dataset[0])
            except Exception:
                raise RuntimeError(f"Could not automatically build the approximator. Please pass a dataset as the "
                                   f"first argument to `approximator.fit()` or manually call `approximator.build()` "
                                   f"with a dictionary specifying your data shapes.")

        return super().fit(*args, **kwargs)