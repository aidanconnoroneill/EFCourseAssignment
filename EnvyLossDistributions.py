import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np


def isEF1(values1, values2, objs1, objs2):
    agent1_net = sum(values1[i] for i in objs1)
    agent2_net = sum(values2[i] for i in objs2)

    agent1_net_other = sum(values1[i] for i in objs2)
    agent2_net_other = sum(values2[i] for i in objs1)
    agent1_best_obj = 0
    if len(objs1) > 0:
        agent1_best_obj = max(values2[i] for i in objs1)
    agent2_best_obj = 0
    if len(objs2) > 0:
        agent2_best_obj = max(values1[i] for i in objs2)

    return (not agent1_net >= agent1_net_other - agent2_best_obj, not agent2_net >= agent2_net_other - agent1_best_obj)


def transfers(giver_values, taker_values, giver_objs, taker_objs):
    best = None
    worst = None

    for i in range(len(taker_values)):
        if i in giver_objs:
            if best is None or giver_values[i] - taker_values[i] < best:
                best = i
            if worst is None or giver_values[i] - taker_values[i] > worst:
                worst = i
    return(best, worst)


def get_value_of_allocation(values1, values2, objs1, objs2):
    return sum(values1[i] for i in objs1) + sum(values2[i] for i in objs2)


def get_envy_reduction(values1, values2, best_case=True):
    ut_max = 0
    for value1, value2 in zip(values1, values2):
        ut_max += max(value1, value2)

    objs1 = []
    objs2 = []
    for i in range(len(values1)):
        if values1[i] >= values2[i]:
            objs1.append(i)
        else:
            objs2.append(i)

    while True:
        agent1Envy, agent2Envy = isEF1(values1, values2, objs1, objs2)
        if not agent1Envy and not agent2Envy:
            break
        if agent1Envy:
            best, worst = transfers(values2, values1, objs2, objs1)
            if best_case:
                objs1.append(best)
                objs2.remove(best)
            else:
                objs1.append(worst)
                objs2.remove(worst)
        if agent2Envy:
            best, worst = transfers(values1, values2, objs1, objs2)
            if best_case:
                objs2.append(best)
                objs1.remove(best)
            else:
                objs2.append(worst)
                objs1.remove(worst)
    return ut_max - get_value_of_allocation(values1, values2, objs1, objs2)


def get_data():
    print(get_envy_reduction([50, 50, 0], [34, 34, 33]))
    print(get_envy_reduction([33, 34, 34], [50, 50, 0]))
    print(get_envy_reduction([33, 34, 34], [0, 50, 50]))
    balls = 100
    envy_reductions = []
    count = 0

    for firstValAgent1 in range(0, balls+1):
        for secondValAgent1 in range(0, firstValAgent1):
            thirdValAgent1 = balls - firstValAgent1 - secondValAgent1
            if thirdValAgent1 <= secondValAgent1 and thirdValAgent1 >= 0:
                for firstValAgent2 in range(0, balls+1):
                    for secondValAgent2 in range(0, balls+1 - firstValAgent2):
                        thirdValAgent2 = balls - firstValAgent2 - secondValAgent2
                        print([firstValAgent1, secondValAgent1, thirdValAgent1], [
                            firstValAgent2, secondValAgent2, thirdValAgent2])
                        reduction = get_envy_reduction([firstValAgent1, secondValAgent1, thirdValAgent1], [
                            firstValAgent2, secondValAgent2, thirdValAgent2])
                        ordering = ""
                        if firstValAgent2 >= secondValAgent2 >= thirdValAgent2:
                            ordering = "a>=b>=c"
                        elif firstValAgent2 >= thirdValAgent2 >= secondValAgent2:
                            ordering = "a>=c>=b"
                        elif secondValAgent2 >= firstValAgent2 >= thirdValAgent2:
                            ordering = "b>=a>=c"
                        elif secondValAgent2 >= thirdValAgent2 >= firstValAgent2:
                            ordering = "b>=c>=a"
                        elif thirdValAgent2 >= firstValAgent2 >= secondValAgent2:
                            ordering = "c>=a>=b"
                        else:
                            ordering = "c>=b>=a"
                        envy_reductions.append((ordering, reduction))

        df = pd.DataFrame(envy_reductions, columns=["Ordering", "Reduction"])
        df.to_csv('envy_reductions.csv')


df = pd.read_csv("envy_reductions.csv")
print(df.head())

df_pivot = df.pivot_table(
    index=['Reduction'], columns='Ordering', fill_value=0, aggfunc='size')
print(df_pivot.head())
vmax = np.max(df_pivot)
vmin = np.min(df_pivot)

ax = sns.heatmap(df_pivot)

cbar = ax.collections[0].colorbar
cbar.set_ticks([0, 100, 1000, 10000])
# sns.heatmap(df_pivot, annot=True)
plt.xticks(rotation=30)
plt.show()
