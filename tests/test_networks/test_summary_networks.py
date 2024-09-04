import keras
import numpy as np
import pytest

from tests.utils import assert_layers_equal


@pytest.mark.parametrize("automatic", [True, False])
def test_build(automatic, summary_network, random_set):
    if summary_network is None:
        pytest.skip()

    assert summary_network.built is False

    if automatic:
        summary_network(random_set)
    else:
        summary_network.build(keras.ops.shape(random_set))

    assert summary_network.built is True

    # check the model has variables
    assert summary_network.variables, "Model has no variables."


def test_variable_batch_size(summary_network, random_set):
    if summary_network is None:
        pytest.skip()

    # build with one batch size
    summary_network.build(keras.ops.shape(random_set))

    # run with another batch size
    batch_sizes = np.random.choice(10, replace=False, size=3)
    for b in batch_sizes:
        new_input = keras.ops.zeros((b,) + keras.ops.shape(random_set)[1:])
        summary_network(new_input)


def test_variable_set_size(summary_network, random_set):
    if summary_network is None:
        pytest.skip()

    # build with one set size
    summary_network.build(keras.ops.shape(random_set))

    # run with another set size
    for _ in range(10):
        b = keras.ops.shape(random_set)[0]
        s = np.random.randint(1, 10)
        new_input = keras.ops.zeros((b, s, keras.ops.shape(random_set)[2]))
        summary_network(new_input)


def test_serialize_deserialize(tmp_path, summary_network, random_set):
    if summary_network is None:
        pytest.skip()

    summary_network.build(keras.ops.shape(random_set))

    keras.saving.save_model(summary_network, tmp_path / "model.keras")
    loaded = keras.saving.load_model(tmp_path / "model.keras")

    assert_layers_equal(summary_network, loaded)

@pytest.mark.parametrize("stage", ["training", "validation"])
def test_compute_metrics(stage, summary_network, random_set):
    if summary_network is None:
        pytest.skip()

    summary_network.build(keras.ops.shape(random_set))

    metrics = summary_network.compute_metrics(random_set, stage=stage)

    assert "outputs" in metrics
    # TODO: check the shape of the outputs (after the call method is implemented)

    if summary_network.base_distribution is not None:
        assert "loss" in metrics
        assert metrics["loss"].shape == ()

        if stage != "training":
            for metric in summary_network.metrics:
                assert metric.name in metrics
                assert metrics[metric.name].shape == ()
