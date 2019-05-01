import objectbox
from tests.model import TestEntity


def test_model():
    model = objectbox.Model()
    model.add_entity(TestEntity)

    builder = objectbox.Builder()
    builder.model(model)
