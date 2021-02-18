import itertools

a1Valuations = {
    "g1": 0.0,
    "g2": .3,
    "g3": 1.7
}
a2Valuations = {
    "g1": .3,
    "g2": .2,
    "g3": 1.5
}
a3Valuations = {
    "g1": .9,
    "g2": .5,
    "g3": .6
}

agentsToValuations = {
    "a1": a1Valuations,
    "a2": a2Valuations,
    "a3": a3Valuations
}


def randomLipton():
    orderAgents = list(itertools.permutations(["a1", "a2", "a3"]))
    orderGoods = list(itertools.permutations(["g1", "g2", "g3"]))

    alloc = {}

    def shouldSwap(a1, a2, alloc):
        if a2 not in alloc:
            return alloc, False
        a1Good = alloc[a1]
        a2Good = alloc[a2]
        changed = False
        if agentsToValuations[a1][a2Good] > agentsToValuations[a1][a1Good] and agentsToValuations[a2][a1Good] > agentsToValuations[a2][a2Good]:
            alloc[a1] = a2Good
            alloc[a2] = a1Good
            changed = True
        return alloc, changed

    i = 0
    a1TotalValue = 0.0
    a1TotalValuea2 = 0.0
    for orderAgent in orderAgents:
        for orderGood in orderGoods:
            alloc = {}
            for agent, good in zip(orderAgent, orderGood):
                alloc[agent] = good
                hasSwapped = True
                while hasSwapped:
                    hasSwapped = False
                    for otherAgent in orderAgent:
                        if otherAgent is agent:
                            pass
                        alloc, hasSwapped = shouldSwap(
                            agent, otherAgent, alloc)

            i += 1
            if "a1" in alloc:
                a1TotalValue += a1Valuations[alloc["a1"]]
            if "a2" in alloc:
                a1TotalValuea2 += a1Valuations[alloc["a2"]]
            print(alloc)

    if a1TotalValue + .001 < a1TotalValuea2:
        print(a1TotalValue)
        print(a1TotalValuea2)
        print(alloc)
        print(a1Valuations)
        print(a2Valuations)
        print(a3Valuations)


randomLipton()
# gs = [0.0 + .1 * i for i in range(10)]
# for a1g1 in gs:
#     for a1g2 in gs:
#         a1g3 = 2.0 - a1g1 - a1g2
#         a1Valuations["g1"] = a1g1
#         a1Valuations["g2"] = a1g2
#         a1Valuations["g3"] = a1g3
#         for a2g1 in gs:
#             for a2g2 in gs:
#                 a2g3 = 2.0 - a2g1 - a2g2
#                 a2Valuations["g1"] = a2g1
#                 a2Valuations["g2"] = a2g2
#                 a2Valuations["g3"] = a2g3
#                 for a3g1 in gs:
#                     for a3g2 in gs:
#                         a3g3 = 2.0 - a3g1 - a3g2
#                         a3Valuations["g1"] = a3g1
#                         a3Valuations["g2"] = a3g2
#                         a3Valuations["g3"] = a3g3
#                         randomLipton()
