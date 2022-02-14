import random
from math import log
from random import uniform

import numpy as np


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


def Poison(t, l0, l1=None):
    """
    Poison discrete distribution simulated via exponentials as in conf
    It can be homogeneous if no l1 is supplied or it can be heterogeneos with an uniform in [l0,l1]
    """
    total = 0
    num = 0
    while total < t:
        num += 1
        l = random.uniform(l0, l1) if l1 is not None else l0
        r = Exponential(l)
        total += r
    return num


def Bernoulli(p):
    """
    bernoulli discrete distribution
    # X ∼ Ber(p)
    """
    u = uniform(0, 1)
    res = 1 if u <= p else 0
    return res


def Normal(mean_p=0, std_p=1):
    """
    Normal distribution simulated via acept-rejection montecarlo algorithm
    """
    density_gen = lambda x, mean, std: (1 / std * np.sqrt(2 * np.pi)) * np.exp((-1 / 2) * ((x - mean) / std) ** 2)
    density_spec = lambda x: density_gen(x, mean_p, std_p)
    xmin = mean_p - 5 * std_p
    xmax = mean_p + 5 * std_p
    ymax = density_spec(mean_p) + 0.2
    while True:
        x = np.random.uniform(low=xmin, high=xmax)
        y = np.random.uniform(low=0, high=ymax)
        if y < density_spec(x):
            return x #, y


# import matplotlib.pyplot as plt
# x, y = map(list, zip(*[Normal() for _ in range(1000)]))
# plt.scatter(x, y)
# plt.show()
