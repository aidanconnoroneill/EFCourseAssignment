import math
import csv
import pandas as pd
import numpy as np
import copy

from itertools import chain, combinations, permutations

from ortools.sat.python import cp_model

possible_valuations = [0, 1, 2, 3]
agents = [0, 1, 2]
items = [0, 1, 2, 3, 4]

# Tested on 2 agents, valuations [0, 1, 2], up to 7 items.  All were EF1
# Tested on 2 agents, valuations [0, 1, 2, 3], up to 7 items.  All were EF1
# Tested on 3 agents, valuations [0, 1, 2], up to 5 items.  All were EF1
# Tested on 3 agents, valuations [0, 1, 2, 3], up to 5 items All were EF1
# When is leximin envy free when is it not


def get_all_valuations_rec(num_items, so_far):
    if len(so_far) == num_items:
        if sum(so_far) == num_items:
            return so_far
        return
    ret = []
    for value in possible_valuations:
        if sum(so_far) + value <= num_items:
            lst = get_all_valuations_rec(
                num_items, copy.deepcopy(so_far) + [value])
            if lst is not None and not len(lst) == 0:
                ret += lst
    return ret


def get_all_valuations(num_items):
    valuations = get_all_valuations_rec(num_items, [])
    ret = []
    current = []
    for i in range(len(valuations)):
        current.append(valuations[i])
        if i % num_items == num_items - 1:
            ret.append(current)
            current = []
    return ret

# Returns whether agent2 envies agent1


def has_envy(assignment, valuations, agent1, agent2):
    best_item = -1
    sum_values = 0
    my_value = 0
    for item in items:
        if assignment[(agent1, item)]:
            sum_values += valuations[(agent2, item)]
            if valuations[(agent2, item)] > best_item:
                best_item = valuations[(agent2, item)]
        if assignment[(agent2, item)]:
            my_value += valuations[(agent2, item)]
    return my_value < sum_values - best_item


def main():
    all_valuations = get_all_valuations(len(items))

    for i in range(0, len(all_valuations)):
        for j in range(i, len(all_valuations)):
            for k in range(j, len(all_valuations)):
                values = (all_valuations[i],
                          all_valuations[j], all_valuations[k])

                model = cp_model.CpModel()
                assignments = {}
                for agent in agents:
                    for item in items:
                        assignments[(agent, item)] = model.NewBoolVar(
                            'item %i is assigned to agent %i' % (item, agent))

                # Course constraints
                for item in items:
                    model.Add(sum(assignments[(agent, item)]
                                  for agent in agents) == 1)

                valuations = {}
                for agent in agents:
                    for item in items:
                        valuations[(agent, item)] = values[agent][item]

                model.Maximize(
                    sum(valuations[(a, i)] * assignments[(a, i)] for i in items
                        for a in agents))

                solver = cp_model.CpSolver()

                solver.Solve(model)

                for agent1 in agents:
                    for agent2 in agents:
                        if has_envy(assignments, valuations, agent1, agent2):
                            print("UHOH")

                # print('Done writing')

                # print()
                # print('Statistics')
                # print('  - conflicts       : %i' % solver.NumConflicts())
                # print('  - branches        : %i' % solver.NumBranches())
                # print('  - Value of items = %i' % solver.ObjectiveValue())

                # print('  - wall time       : %f s' % solver.WallTime())


if __name__ == "__main__":
    main()
