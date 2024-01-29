# -*- coding: utf-8 -*-
"""minbuses (1).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1xBLuwbaGCzX2jaMZtqR8DsCC5hxtOush
"""

import pandas as pd
import numpy as np
import networkx as nx
import osmnx as ox
import cplex

import datetime

!pip install cplex

pip install numpy==1.23

pip install pandas==1.5.3

pip install osmnx

from zipfile import ZipFile
file_name = "OneDrive_2023-03-29.zip"

with ZipFile(file_name, 'r') as zip:
  zip.extractall()
  print('Done')

trip_data = pd.read_csv(r"128 Business Council GTFS/trips.txt")
    stops_data = pd.read_csv(r"128 Business Council GTFS/stops.txt")
    stops_times_data = pd.read_csv(r"128 Business Council GTFS/stop_times.txt")
    routes_data = pd.read_csv(r"128 Business Council GTFS/routes.txt")

# stops_times_data

result2 = stops_times_data.groupby('trip_id').agg(
    {
        'stop_id': ['first', 'last'], 
        'arrival_time': 'last', 
        'departure_time': 'first'
    }
)

result2[("arrival_time",'last')] = pd.to_datetime(result2[("arrival_time",'last')],errors = "coerce")
result2[("departure_time",'first')] = pd.to_datetime(result2[("departure_time",'first')],errors = "coerce")

result2 = result2.reset_index()

depot = result2[('stop_id', 'first')].value_counts().reset_index()

print("depot is stop number ", depot["index"][0] )

origin_with_depot = result2.loc[result2[('stop_id', 'first')] == depot["index"][0]].index.tolist()
# origin_with_depot
# for these trips deadhead will be zero so c_74_2 will be zero

origin_without_depot = result2.loc[result2[('stop_id', 'first')] != depot["index"][0]].index.tolist()

dest_with_depot = result2.loc[result2[('stop_id', 'last')] == depot["index"][0]].index.tolist()
# dest_with_depot
# for these trips deadhead will be zero so c_0_74 will be zero

unique_values = pd.concat([result2[('stop_id', 'first')], result2[('stop_id', 'last')]]).unique().tolist()
# unique_values

li1 = []
    df = stops_data[stops_data["stop_id"].isin(unique_values)]
    for idd, row in df.iterrows():
        li1.append((row.stop_id,row.stop_lon,row.stop_lat))

# li1

G = ox.graph_from_place("Waltham", network_type="drive")

# G = ox.project_graph(G)
stop_node = {}
for i in range(len(li1)):
  stop_node[li1[i][0]] = ox.nearest_nodes(G, li1[i][1], li1[i][2])

distance = {}

for i in stop_node:
  distance[i] = {}
  for j in stop_node:
              distance[i][j] = (nx.shortest_path_length(G, source = stop_node[i], target = stop_node[j], weight='length', method ='dijkstra'))/8.33


# velocity = 30

trips_origin = []
for i in origin_without_depot:
  dest = result2.iloc[i]['stop_id']['first']
  origin = depot["index"][0]
  trips_origin.append((len(result2),i,distance[origin][dest]))

# trips_origin

# distance

trips = []
for index1, row1 in result2.iterrows():
#     t1_first_stop = row1['stop_id']['first']
    t1_last_stop = row1['stop_id']['last']
    t1_arrival_time = row1['arrival_time']['last']
    for index2, row2 in result2.iterrows():
        t2_first_stop = row2['stop_id']['first']
#         t2_last_stop = row2['stop_id']['last']
        t2_departure_time = row2['departure_time']['first']
        if index1 != index2:
            # print(t1_last_stop)
            # print(t2_first_stop)
            if t1_arrival_time + datetime.timedelta(seconds=distance[t1_last_stop][t2_first_stop]) <= t2_departure_time:
                trips.append((index1,index2,distance[t1_last_stop][t2_first_stop]))

"""# optimization model

# model for bus minimization
"""

model = cplex.Cplex()
model.objective.set_sense(model.objective.sense.minimize)

sorted_trips = sorted(trips, key=lambda x: x[1])

# sorted_trips

dec_var = ["x"+str(row[0])+"_"+str(row[1]) for row in trips]
# dec_var = []
for row in origin_with_depot:
  dec_var.append("x"+str(len(result2))+"_"+str(row))
for row in dest_with_depot:
  dec_var.append("x"+str(row)+"_"+str(len(result2)))
for row in trips_origin:
  dec_var.append("x"+str(row[0])+"_"+str(row[1]))
# decision variable



obj = [1 for row in dec_var]

lb = [0 for i in range(len(dec_var))] # lower bound
ub = [1 for i in range(len(dec_var))] # upper bound
type_int =  ["I" for i in range(len(dec_var))]

model.variables.add(obj=obj, lb=lb, ub=ub, names=dec_var, types= type_int)

constraint_names = ["c1"]
first_constraint = [["x"+str(len(result2))+"_"+str(row) for row in origin_with_depot] 
                    + ["x"+str(row[0])+"_"+str(row[1]) for row in trips_origin],
                    [1 for row in origin_with_depot]+[1 for row in trips_origin]]
constraints = [first_constraint]
constraint_direction = ["L"]
rhs = [24]

model.linear_constraints.add(lin_expr=constraints, senses=constraint_direction, rhs=rhs, names=constraint_names)

prev_node = trips[0][0]
k=3
constraints_out = {}
for i in range(len(result2)):
  constraints_out["constraint_"+str(i)] = [[],[]]
for row in trips:
  
  if prev_node == row[0]:
    constraints_out["constraint_"+str(row[0])][0].append("x"+str(row[0])+"_"+str(row[1]))
    constraints_out["constraint_"+str(row[0])][1].append(1)
  else:
    constraints_out["constraint_"+str(row[0])][0].append("x"+str(row[0])+"_"+str(row[1]))
    constraints_out["constraint_"+str(row[0])][1].append(1)
    if prev_node in dest_with_depot:
      constraints_out["constraint_"+str(prev_node)][0].append("x"+str(prev_node)+"_"+str(len(result2)))
      constraints_out["constraint_"+str(prev_node)][1].append(1)
    prev_node = row[0]

if trips[-1][0] in dest_with_depot:
    constraints_out["constraint_"+str(trips[-1][0])][0].append("x"+str(trips[-1][0])+"_"+str(len(result2)))
    constraints_out["constraint_"+str(trips[-1][0])][1].append(1)

for trip in sorted_trips:
  if trip[1] in dest_with_depot and len(constraints_out["constraint_"+str(trip[1])][0])== 0:
    # print(trip)
    constraints_out["constraint_"+str(trip[1])][0].append("x"+str(trip[1])+"_"+str(len(result2)))
    constraints_out["constraint_"+str(trip[1])][1].append(1)

c_out = [constraints_out["constraint_"+str(row)] for row in range(len(constraints_out)) if constraints_out["constraint_"+str(row)][0] != []]
constraint_direction = []
rhs = []
constraint_names = []
for i in range(3,len(c_out)+3):
  constraint_names.append("c_out"+str(i))
for i in range(len(c_out)):
  constraint_direction.append("E")
  rhs.append(1)
model.linear_constraints.add(lin_expr=c_out, senses=constraint_direction, rhs=rhs, names=constraint_names)

x_ij_names = []
x_hi_names = []
for row in origin_with_depot:
  x_ij_names.append("x"+str(len(result2))+"_"+str(row))
for row in trips_origin:
  x_ij_names.append("x"+str(row[0])+"_"+str(row[1]))
for row in dest_with_depot:
  x_hi_names.append("x"+str(row)+"_"+str(len(result2)))

demand_constaint = cplex.SparsePair(ind=x_ij_names+x_hi_names, val=[1.0]*len(x_ij_names) + [-1.0]*len(x_hi_names))
model.linear_constraints.add(lin_expr=[demand_constaint], senses=["E"], rhs=[0.0],names = ["c2"])

# x_ij_names

# sorted_trips = sorted(trips, key=lambda x: x[1])

prev_node = trips[1][0]
k=3
constraints_in = {}
for i in range(len(result2)):
  constraints_in["constraint_"+str(i)] = [[],[]]
for row in sorted_trips:
  if prev_node == row[1]:
    constraints_in["constraint_"+str(row[1])][0].append("x"+str(row[0])+"_"+str(row[1]))
    constraints_in["constraint_"+str(row[1])][1].append(1)
  else:
    constraints_in["constraint_"+str(row[1])][0].append("x"+str(row[0])+"_"+str(row[1]))
    constraints_in["constraint_"+str(row[1])][1].append(1)
    if prev_node in origin_with_depot:
      constraints_in["constraint_"+str(prev_node)][0].append("x"+str(len(result2))+"_"+str(prev_node))
      constraints_in["constraint_"+str(prev_node)][1].append(1)
    prev_node = row[1]
if sorted_trips[-1][1] in origin_with_depot:
    constraints_in["constraint_"+str(sorted_trips[-1][1])][0].append("x"+str(len(result2))+"_"+str(sorted_trips[-1][1]))
    constraints_in["constraint_"+str(sorted_trips[-1][1])][1].append(1)

for trip in trips:
  if trip[0] in origin_with_depot and len(constraints_in["constraint_"+str(trip[0])][0])== 0:
    print(trip)
    constraints_in["constraint_"+str(trip[0])][0].append("x"+str(len(result2))+"_"+str(str(trip[0])))
    constraints_in["constraint_"+str(trip[0])][1].append(1)
c_in = [constraints_in["constraint_"+str(row)] for row in range(len(constraints_in)) if constraints_in["constraint_"+str(row)][0] != []]

for trip in trips_origin:
  # if trip[0] in origin_with_depot and len(constraints_in["constraint_"+str(trip[0])][0])== 0:
  #   print(trip)
    constraints_in["constraint_"+str(trip[1])][0].append("x"+str(len(result2))+"_"+str(str(trip[1])))
    constraints_in["constraint_"+str(trip[1])][1].append(1)
c_in = [constraints_in["constraint_"+str(row)] for row in range(len(constraints_in)) if constraints_in["constraint_"+str(row)][0] != []]
constraint_direction = []
rhs = []
constraint_names = []
for i in range(3,len(c_in)+3):
  constraint_names.append("c_in"+str(i))
for i in range(len(c_in)):
  constraint_direction.append("E")
  rhs.append(1)

# c_in

model.linear_constraints.add(lin_expr=c_in, senses=constraint_direction, rhs=rhs, names=constraint_names)

flow_conservation = {}
for i in range(len(result2)):
  flow_conservation[i] = []
# for i in range(len(result2)):
#   constraints_out["constraint_"+str(i)] = [[],[]]
for i in range(len(result2)):
  if "constraint_"+str(i) in constraints_out and "constraint_"+str(i) in constraints_in:
    flow_conservation[i].append(constraints_out["constraint_"+str(i)][0]+ constraints_in["constraint_"+str(i)][0])
    flow_conservation[i].append(constraints_out["constraint_"+str(i)][1] + [-x for x in constraints_in["constraint_"+str(i)][1]])

c_flow = [flow_conservation[row] for row in range(len(flow_conservation))if flow_conservation[row][0] != []]
constraint_direction = []
rhs = []
constraint_names = []
for i in range(3,len(c_flow)+3):
  constraint_names.append("c_flow"+str(i))
for i in range(len(c_flow)):
  constraint_direction.append("E")
  rhs.append(0)
model.linear_constraints.add(lin_expr=c_flow, senses=constraint_direction, rhs=rhs, names=constraint_names)

model.write("example1.lp")

model = cplex.Cplex("example1.lp")
# model.solve()

# print(model.solution.get_values())

# print(model.solution.get_objective_value())

model.solution.write("output1.sol")

"""# model for cost *minimization*"""



model = cplex.Cplex()
model.objective.set_sense(model.objective.sense.minimize)

sorted_trips = sorted(trips, key=lambda x: x[1])

# sorted_trips

dec_var = ["x"+str(row[0])+"_"+str(row[1]) for row in trips]
# dec_var = []
for row in origin_with_depot:
  dec_var.append("x"+str(len(result2))+"_"+str(row))
for row in dest_with_depot:
  dec_var.append("x"+str(row)+"_"+str(len(result2)))
for row in trips_origin:
  dec_var.append("x"+str(row[0])+"_"+str(row[1]))
# decision variable

obj = [row[2] for row in trips]
for row in origin_with_depot:
  obj.append(0)
for row in dest_with_depot:
  obj.append(0)
for row in trips_origin:
  obj.append(row[2])
# objective

lb = [0 for i in range(len(dec_var))] # lower bound
ub = [1 for i in range(len(dec_var))] # upper bound
type_int =  ["I" for i in range(len(dec_var))]

model.variables.add(obj=obj, lb=lb, ub=ub, names=dec_var, types= type_int)

"""#capacity"""

constraint_names = ["c1"]
first_constraint = [["x"+str(len(result2))+"_"+str(row) for row in origin_with_depot] 
                    + ["x"+str(row[0])+"_"+str(row[1]) for row in trips_origin],
                    [1 for row in origin_with_depot]+[1 for row in trips_origin]]
constraints = [first_constraint]
constraint_direction = ["L"]
rhs = [24]

model.linear_constraints.add(lin_expr=constraints, senses=constraint_direction, rhs=rhs, names=constraint_names)

"""#outgoing flow"""

prev_node = trips[0][0]
k=3
constraints_out = {}
for i in range(len(result2)):
  constraints_out["constraint_"+str(i)] = [[],[]]
for row in trips:
  
  if prev_node == row[0]:
    constraints_out["constraint_"+str(row[0])][0].append("x"+str(row[0])+"_"+str(row[1]))
    constraints_out["constraint_"+str(row[0])][1].append(1)
  else:
    constraints_out["constraint_"+str(row[0])][0].append("x"+str(row[0])+"_"+str(row[1]))
    constraints_out["constraint_"+str(row[0])][1].append(1)
    if prev_node in dest_with_depot:
      constraints_out["constraint_"+str(prev_node)][0].append("x"+str(prev_node)+"_"+str(len(result2)))
      constraints_out["constraint_"+str(prev_node)][1].append(1)
    prev_node = row[0]

if trips[-1][0] in dest_with_depot:
    constraints_out["constraint_"+str(trips[-1][0])][0].append("x"+str(trips[-1][0])+"_"+str(len(result2)))
    constraints_out["constraint_"+str(trips[-1][0])][1].append(1)

for trip in sorted_trips:
  if trip[1] in dest_with_depot and len(constraints_out["constraint_"+str(trip[1])][0])== 0:
    # print(trip)
    constraints_out["constraint_"+str(trip[1])][0].append("x"+str(trip[1])+"_"+str(len(result2)))
    constraints_out["constraint_"+str(trip[1])][1].append(1)

c_out = [constraints_out["constraint_"+str(row)] for row in range(len(constraints_out)) if constraints_out["constraint_"+str(row)][0] != []]
constraint_direction = []
rhs = []
constraint_names = []
for i in range(3,len(c_out)+3):
  constraint_names.append("c_out"+str(i))
for i in range(len(c_out)):
  constraint_direction.append("E")
  rhs.append(1)
model.linear_constraints.add(lin_expr=c_out, senses=constraint_direction, rhs=rhs, names=constraint_names)

"""# depot flow conservation"""

x_ij_names = []
x_hi_names = []
for row in origin_with_depot:
  x_ij_names.append("x"+str(len(result2))+"_"+str(row))
for row in trips_origin:
  x_ij_names.append("x"+str(row[0])+"_"+str(row[1]))
for row in dest_with_depot:
  x_hi_names.append("x"+str(row)+"_"+str(len(result2)))

demand_constaint = cplex.SparsePair(ind=x_ij_names+x_hi_names, val=[1.0]*len(x_ij_names) + [-1.0]*len(x_hi_names))
model.linear_constraints.add(lin_expr=[demand_constaint], senses=["E"], rhs=[0.0],names = ["c2"])

"""# incoming flows"""

prev_node = trips[1][0]
k=3
constraints_in = {}
for i in range(len(result2)):
  constraints_in["constraint_"+str(i)] = [[],[]]
for row in sorted_trips:
  if prev_node == row[1]:
    constraints_in["constraint_"+str(row[1])][0].append("x"+str(row[0])+"_"+str(row[1]))
    constraints_in["constraint_"+str(row[1])][1].append(1)
  else:
    constraints_in["constraint_"+str(row[1])][0].append("x"+str(row[0])+"_"+str(row[1]))
    constraints_in["constraint_"+str(row[1])][1].append(1)
    if prev_node in origin_with_depot:
      constraints_in["constraint_"+str(prev_node)][0].append("x"+str(len(result2))+"_"+str(prev_node))
      constraints_in["constraint_"+str(prev_node)][1].append(1)
    prev_node = row[1]
if sorted_trips[-1][1] in origin_with_depot:
    constraints_in["constraint_"+str(sorted_trips[-1][1])][0].append("x"+str(len(result2))+"_"+str(sorted_trips[-1][1]))
    constraints_in["constraint_"+str(sorted_trips[-1][1])][1].append(1)

for trip in trips:
  if trip[0] in origin_with_depot and len(constraints_in["constraint_"+str(trip[0])][0])== 0:
    print(trip)
    constraints_in["constraint_"+str(trip[0])][0].append("x"+str(len(result2))+"_"+str(str(trip[0])))
    constraints_in["constraint_"+str(trip[0])][1].append(1)
c_in = [constraints_in["constraint_"+str(row)] for row in range(len(constraints_in)) if constraints_in["constraint_"+str(row)][0] != []]

for trip in trips_origin:
  # if trip[0] in origin_with_depot and len(constraints_in["constraint_"+str(trip[0])][0])== 0:
  #   print(trip)
    constraints_in["constraint_"+str(trip[1])][0].append("x"+str(len(result2))+"_"+str(str(trip[1])))
    constraints_in["constraint_"+str(trip[1])][1].append(1)
c_in = [constraints_in["constraint_"+str(row)] for row in range(len(constraints_in)) if constraints_in["constraint_"+str(row)][0] != []]
constraint_direction = []
rhs = []
constraint_names = []
for i in range(3,len(c_in)+3):
  constraint_names.append("c_in"+str(i))
for i in range(len(c_in)):
  constraint_direction.append("E")
  rhs.append(1)

model.linear_constraints.add(lin_expr=c_in, senses=constraint_direction, rhs=rhs, names=constraint_names)

"""# flow conservation

"""

flow_conservation = {}
for i in range(len(result2)):
  flow_conservation[i] = []
# for i in range(len(result2)):
#   constraints_out["constraint_"+str(i)] = [[],[]]
for i in range(len(result2)):
  if "constraint_"+str(i) in constraints_out and "constraint_"+str(i) in constraints_in:
    flow_conservation[i].append(constraints_out["constraint_"+str(i)][0]+ constraints_in["constraint_"+str(i)][0])
    flow_conservation[i].append(constraints_out["constraint_"+str(i)][1] + [-x for x in constraints_in["constraint_"+str(i)][1]])

c_flow = [flow_conservation[row] for row in range(len(flow_conservation))if flow_conservation[row][0] != []]
constraint_direction = []
rhs = []
constraint_names = []
for i in range(3,len(c_flow)+3):
  constraint_names.append("c_flow"+str(i))
for i in range(len(c_flow)):
  constraint_direction.append("E")
  rhs.append(0)
model.linear_constraints.add(lin_expr=c_flow, senses=constraint_direction, rhs=rhs, names=constraint_names)

model.write("example2.lp")

model = cplex.Cplex("example2.lp")
model.solve()

model.solution.write("output2.sol")

G = nx.DiGraph()
# G.add_node("a", demand=-5)
# G.add_node("d", demand=5)
# G.add_edge("a", "b", weight=3, capacity=4)
# G.add_edge("a", "c", weight=6, capacity=10)
# G.add_edge("b", "d", weight=1, capacity=9)
# G.add_edge("c", "d", weight=2, capacity=5)
# flowDict = nx.min_cost_flow(G)

G = nx.DiGraph()
""" part 1"""
G.add_node(len(result2), demand=-12)
G.add_node(len(result2)+1,demand = 12)
for row in trips:
  G.add_edge(row[0], row[1], weight=1, capacity=1)
for row in origin_with_depot:
  G.add_edge(len(result2), row, weight=0, capacity=1)
for row in dest_with_depot:
  G.add_edge(row,len(result2)+1, weight=0, capacity=1)
for row in trips_origin:
  G.add_edge(len(result2),row[1], weight=1, capacity=1)

flowDict = nx.min_cost_flow(G)

flowDict

G = nx.DiGraph()
""" part 2"""
G.add_node(len(result2), demand=-17)
G.add_node(len(result2)+1,demand = 17)
for row in trips:
  G.add_edge(row[0], row[1], weight=row[2], capacity=1)
for row in origin_with_depot:
  G.add_edge(len(result2), row, weight=0, capacity=1)
for row in dest_with_depot:
  G.add_edge(row,len(result2)+1, weight=0, capacity=1)
for row in trips_origin:
  G.add_edge(len(result2),row[1], weight=row[2], capacity=1)

flowDict = nx.min_cost_flow(G)

flowDict
