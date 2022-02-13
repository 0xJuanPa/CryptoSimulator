class CoinGenericTemplate:
    def __init__(self, name, *, initial_miners, base_value):
        self.name = name
        self.miners: int = initial_miners
        self.value: int = base_value
        self.base_value = base_value
        self.block_size: int = 1
        self.queue: list = list()
        self.transactions: set = set()

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
        res = f"{self.name} miners {self.miners} value {self.value}"
        return res

    def validate(self):
        '''
        Como el poder de computo es la suma de todos los mineros es analogo decir que cada minero valide una transacion
        '''
        pass

    def update_parameters(self):
        pass
