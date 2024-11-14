import matplotlib.pyplot as plt
import networkx as nx
from itertools import count
import matplotlib.patches as mpatches
from matplotlib import pylab


class IfcEntity:
    def __init__(self, data):
        self.ifctype = data["ifc_type"]
        self.id = data["id"]

    def __str__(self):
        return "#" + str(self.id) + "_" + self.ifctype

    __repr__ = __str__


def get_cmap(n, name="hsv"):
    """Returns a function that maps each index in 0, 1, ..., n-1 to a distinct
    RGB color; the keyword argument name must be a standard mpl colormap name."""
    return plt.cm.get_cmap(name, n)


G = nx.Graph()

colors = []
color_map = []

ifctypes = set()

types_color = {}

for e in ents.values():
    for r in e["attributes"][1]:
        G.add_edge(e["id"], r)
        color_map.append("red")
        ifctypes.add(e["ifc_type"])
        ifctypes.add(ents[r]["ifc_type"])


cmap = get_cmap(len(ifctypes), "rainbow")

colors = [cmap(i) for i in range(len(ifctypes))]

type_color_mapping = {}

cols = []

i = 0
for eid in G.nodes():
    t = ents[eid]["ifc_type"]
    # print(t)
    if t in type_color_mapping.keys():
        cols.append(type_color_mapping[t])
    else:
        type_color_mapping[t] = colors[i]
        i = i + 1
        cols.append(type_color_mapping[t])


# k controls the distance between the nodes and varies between 0 and 1
# iterations is the number of times simulated annealing is run
# default k=0.1 and iterations=50
pos = nx.spring_layout(G, k=0.8, iterations=60)  # positions for all nodes

nodes = G.nodes()
print(get_cmap(len(nodes)))
cmap = get_cmap(len(nodes))

c_map = [cmap(i) for i in range(len(nodes))]

nc = nx.draw_networkx_nodes(G, pos, nodelist=nodes, node_color=cols, node_size=200)

# edges
elarge = [(u, v) for (u, v, d) in G.edges(data=True)]
nx.draw_networkx_edges(G, pos, edgelist=elarge, width=1)

nx.draw_networkx_labels(G, pos, font_size=8, font_family="sans-serif")


red_patch = mpatches.Patch(color="red", label="The red data")
blue_patch = mpatches.Patch(color="blue", label="The blue data")

patches = []
for k, v in type_color_mapping.items():
    patches.append(mpatches.Patch(color=v, label=k))


plt.legend(handles=patches, fontsize=8)
plt.axis("off")
plt.show()
