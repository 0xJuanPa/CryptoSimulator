class CoinGenericTemplate:
    def __init__(self, name, *, initial_miners, initial_value):
        self.name = name
        self.miners: int = initial_miners
        self.value: int = initial_value
        self.block_size: int = 1
        self.queue: list = list()
        self.transactions: set = set()

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
