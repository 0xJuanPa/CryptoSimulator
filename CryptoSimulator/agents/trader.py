class TraderGenericTemplate:

    def __init__(self,name,*, initial_money):
        self.money = initial_money
        self.wallet : dict[str,int] = dict()

    def trade(self):
        pass


    def analyze_coin_load(self, coin):
        '''
        is intended to eval how much the action will be commited
        '''
        pass