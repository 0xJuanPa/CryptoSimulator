import random

def pick_cheaper_coin(wallet):
    '''
    returns the cheaper coin
    '''
    max_coin = None
    for coin in wallet:
        pass



def pick_expensier_coin(wallet):
    '''
    returns the expensier coin
    '''

def pick_random_coin(wallet):
    '''
    returns a random coin
    '''
    res = random.choice(wallet)
    return res

def get_with_more_utility(my):
    '''
    returns original purhase price, this make an agent non reactive only as now it keeps track
    '''
    pass

def buy(my,coin,amount):
    pass


def sell(my,coin,amount):
    my.money += coin.value * amount
    my.wallet.remove(coin)



def leave(my):
    '''
    sells all coins and abandon the simulation
    '''
    for amount,coin in my.wallet:
        sell(my,coin,amount)
    return

