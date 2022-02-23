import random
import logging
logging.basicConfig(filename="output.log",filemode="w",level=logging.INFO)


from interpreter.tree_interpreter import TrowableReturnContainer


def dummy(func):
    # just for testing interops this will receive a managed function
    res = func(5, 6)
    print(f"called managed func, res {res}")


def say(str):
    '''
    alias for python print
    '''
    logging.info(str)


def pick_coin(idx, wallet):
    '''
    picks a coin given an 1-based index
    '''
    wallet = list(wallet.keys()) if isinstance(wallet, dict) else wallet
    return wallet[idx - 1]


def pick_cheaper_coin(wallet):
    '''
    returns the cheaper coin
    '''
    wallet = list(wallet.keys()) if isinstance(wallet, dict) else wallet
    return min(wallet) if wallet else 0


def pick_expensier_coin(wallet):
    '''
    returns the expensier coin
    '''
    wallet = list(wallet.keys()) if isinstance(wallet, dict) else wallet
    return max(wallet) if wallet else 0


def pick_random_coin(wallet):
    '''
    returns a random coin
    '''
    wallet = list(wallet.keys()) if isinstance(wallet, dict) else wallet
    res = random.choice(wallet) if len(wallet) else 0
    return res


def get_with_more_utility(*, my):
    '''
    returns the coin more suitable for sell 0 if there is no one suitable
    '''
    max = 0
    for coin, (amount, purchased_price, time) in my.wallet.items():
        if coin.value > purchased_price:
            if max:
                if max[1] < coin.value - purchased_price:
                    max = coin, coin.value - purchased_price
            else:
                max = coin, coin.value - purchased_price
    return max[0] if max else 0


def buy(coin, amount=None, *, my, market):
    if amount == 0:
        return
    if amount is None:
        amount = random.uniform(1, max(my.money,1))
    if amount == "all":
        amount = my.money
    purchased = amount / coin.value
    msg = f"{market.time} {repr(my)} Attempt Buy {amount} = {purchased} in {coin.name}"
    if coin in my.wallet:
        prev = my.wallet[coin]
        my.wallet[coin] = (prev[0] + purchased, (prev[1] + coin.value) / 2, market.time)
    else:
        my.wallet[coin] = (purchased, coin.value, market.time)
    my.money -= amount
    if my.money < 0.0001:
        my.money = 0  # avoid numerical errors on iee754 double
    if market.verbose:
        logging.info(msg + f" -> After Money {my.money} , Wallet {my.wallet}")


def sell(coin, amount=None, *, my, market):
    """
    sells an amount of the coin in wallet if not amount is supplied then it will take one randomply
    """
    if amount == 0:
        return
    if amount is None:
        amount = random.uniform(0.0001, max(my.wallet[coin][0],0.0001))
    if amount == "all":
        amount = my.wallet[coin][0]
    msg = f"{market.time} {repr(my)} Attempt Sell {amount} of {coin.name}"
    purchase = my.wallet[coin]
    after_purchase = ((purchase[0] - amount),) + purchase[1:]
    if after_purchase[0] <= 0:
        my.money += coin.value * purchase[0]
        del my.wallet[coin]
    else:
        my.money += coin.value * amount
        my.wallet[coin] = after_purchase
    if market.verbose:
        logging.info(msg + f" -> After Money {my.money} , Wallet {my.wallet}")


def leave(*, my, market):
    '''
    sells all coins and abandon the simulation
    '''
    w = list(my.wallet.items())
    for coin, (amount, price, time) in w:
        sell(coin, amount, my=my, market=market)
    market.leaved.add(my)
    if market.verbose:
        logging.info(f"{repr(my)} Left, Arrived with {my.initial_money} ")
    raise TrowableReturnContainer(None)
