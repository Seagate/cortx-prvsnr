from provisioner import serialize
from provisioner import values
import attr


class SomePrvsnrClass1(serialize.PrvsnrType):
    def __init__(self, attr1, attr2=2, attr3='123'):
        self.attr1 = attr1
        self.attr2 = attr2
        self.attr3 = attr3

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self == other


@attr.s(auto_attribs=True)
class SomePrvsnrClass2(serialize.PrvsnrType):
    attr1: str = attr.ib(default=None)
    attr2: str = attr.ib(default='store')
    attr3: str = attr.ib(init=False, default='')

    def to_args(self):
        return (
            None,
            attr.asdict(self, filter=lambda attr, _: attr.name != 'attr3')
        )


def test_serialize_simple():
    obj1 = SomePrvsnrClass1(3, 4)
    obj1_json = serialize.dumps(obj1)
    obj2 = serialize.loads(obj1_json)
    assert obj1 == obj2


def test_serialize_attr_cls():
    obj1 = SomePrvsnrClass2(3, 4)
    obj1_json = serialize.dumps(obj1)
    obj2 = serialize.loads(obj1_json)
    assert obj1 == obj2


def test_special_values_serialization():
    for value in values._values.values():
        _json = serialize.dumps(value)
        value2 = serialize.loads(_json)
        assert value2 is value
