import math
import random

def get_prob_from_c(C):
    if not isinstance(C, float):
        C = float(C)

    pProcOnN = 0.0
    pProcByN = 0.0
    sumNpProcOnN = 0.0

    maxFails = int(math.ceil(1.0 / C))

    for N in range(1, maxFails + 1):
        pProcOnN = min(1.0, N * C) * (1.0 - pProcByN)
        pProcByN += pProcOnN
        sumNpProcOnN += N * pProcOnN

    return (1.0 / sumNpProcOnN)


def get_c_from_proba(p):
    if not isinstance(p, float):
        p = float(p) # double precision

    Cupper = p
    Clower = 0.0
    Cmid = 0.0
    p2 = 1.0

    while(True):
        Cmid = (Cupper + Clower) / 2.0
        p1 = get_prob_from_c(Cmid)

        if math.fabs(p1 - p2) <= 0:
            break

        if p1 > p:
            Cupper = Cmid
        else:
            Clower = Cmid

        p2 = p1

    return Cmid


def c_to_p(c):
    ev = c

    prob = c

    n = int(np.ceil(1 / c))

    cum_prod = 1

    for x in range(2, n):
        cum_prod *= 1 - (x - 1) * c
        prob_x = cum_prod * (x * c)
        prob += prob_x
        ev += x * prob_x

    prob_x = 1 - prob
    ev += n * prob_x

    return 1 / ev


import random

a_list = [0, 1]
a = 0.99
distribution = [a, 1 - a]

random_number = random.choices(a_list, distribution)

print(random_number)

