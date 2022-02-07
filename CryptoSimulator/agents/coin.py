class CoinGenericTemplate:
    def __init__(self,*,initial_miners,initial_value):
        self.miners: int = 1
        self.transactions: set = set()
        self.queue: list = list()
        self.value: int = 1
        self.block_size: int = 1

    def validate(self):
        '''
        Como el poder de computo es la suma de todos los mineros es analogo decir que cada minero valide una transacion
        '''
        pass

    def update_parameters(self):
        pass
