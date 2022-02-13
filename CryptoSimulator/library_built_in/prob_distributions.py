from math import log
from random import uniform

# First conf of simulation


def Uniform(lower=0, upper=1):
    '''
    # X ∼ U(a, b)~(b − a)U + a
    # can div to floor with 1 to get one discrete uniform with // 1 operation
    '''
    u = uniform(0, 1)
    res = lower + (upper - lower) * u
    return res


def Exponential(l):
    """
    l:lambda
    exponential distribution params.. simulated via inverse transform
    X ~ −(1/λ)ln(U)
    """
    u = uniform(0, 1)
    res = -(1 / l) * log(u)
    return res


def HPoison(l,t):
    """
    Homogene Poison discrete distribution params.. simulated via exponentials as in conf
    """
    pass


def Bernoulli(p):
    """
    bernoulli discrete distribution
    # X ∼ Ber(p)
    """
    u = uniform(0, 1)
    res = 1 if u <= p else 0
    return res


def Normal():
    """
    Normal distribution simulated via acept-rejection
    """
    pass
