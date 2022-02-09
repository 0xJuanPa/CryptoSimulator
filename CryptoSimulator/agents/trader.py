class TraderGenericTemplate:

    def __init__(self,name,*, initial_money):
        self.money = initial_money
        self.wallet : dict[str,int] = dict()

    def trade(self):
        pass




class TraderGeneticTemplate(TraderGenericTemplate):
    def __init__(self,name,*,initial_money):
        super().__init__()
