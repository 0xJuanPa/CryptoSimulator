class CoinGenericTemplate:
    def __init__(self, name, *, base_value):
        self.name = name
        self.value: int = base_value
        self.base_value = base_value

    def __gt__(self, other):
        if not isinstance(other, CoinGenericTemplate):
            raise Exception("Type Error")
        return self.value > other.value

    def __lt__(self, other):
        return other.value > self.value

    def __eq__(self, other):
        if not isinstance(other, CoinGenericTemplate):
            raise Exception("Type Error")
        return other.value == self.value

    def __ge__(self, other):
        return self > other or self == other

    def __le__(self, other):
        return self < other or self == other

    def __hash__(self):
        return hash(self.name)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __repr__(self):
        res = f"{self.name} value {self.value}"
        return res

    def update_parameters(self):
        pass
