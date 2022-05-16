import networkx as nx

G = nx.DiGraph()
G.add_nodes_from(list(range(5)))

nx.add_star(G, [0, 6, 7, 8])

print(G.nodes)
print(G.succ[0])
