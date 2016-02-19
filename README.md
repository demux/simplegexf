# Simple GEXF
A simple `.gexf` parser / writer for python

**Notice:** This is currently work in progress, and I hope to be able to create documentation in the future when I've settled on the overall structure.

## Motivation:
The official [`pygexf`](https://github.com/paulgirard/pygexf) is poorly maintained and almost not documented at all. I needed a simple abstraction layer for the `XML` format for my project.
This project uses [`xmltodict`](https://github.com/martinblech/xmltodict), which means it's much easier to understand and debug than `pygexf` which uses `lxml`.
This is a tool for those who'd rather spend their time learning about something more interesting and worthwhile than `XML`.


## Usage:

~~~python
from simplegexf import Gexf, Edge

gexf = Gexf('tags.gexf')

try:
    graph = gexf.graphs[0]
except IndexError:
    graph = gexf.add_graph(defaultedgetype="directed")

# Define Graph attributes
graph.define_attributes([
    ('description', 'string'),
    ('count', 'integer'),
])

# Define Edge attributes for Graph
graph.define_attributes([
    ('relation_type', 'string'),
], _class='edge')

nodes = {node.id: node for node in graph.nodes}

tags = [
    {
        id: 0,
        name: 'Test tag 1',
        description: 'This is a test tag',
    },
    {
        id: 1,
        name: 'Test tag 2',
        description: 'This is a test tag',
        parents: [0],
    },
    {
        id: 2,
        name: 'Test tag 3',
        description: 'This is a test tag',
        parents: [0, 1],
    }
]

# Create nodes for tags:
for tag in tags:
    try:
        # See if node exists:
        node = nodes[str(tag['id'])]
    except KeyError:
        # Create a new node:
        node = self.graph.add_node(id=str(tag['id']), label=tag['name'])

    # Update node:
    node.set('viz:size', value=10.0)
    node.set('viz:color', r=130, g=130, b=130)

    # Update node attributes:
    for attr in self.graph.node_attributes.keys():
        try:
            node.attributes[attr] = tag[attr]
        except KeyError:
            try:
                del node.attributes[attr]
            except IndexError:
                pass

nodes = {node.id: node for node in graph.nodes}

# Create edges for tags:
for tag in tags:
    try:
        for parent_id in tag['parents']:
            edge = Edge(parent_id, tag['id'])
            graph.edges.append(edge)
            # Attributes are not available before adding edge to graph
            edge.attributes['relation_type'] = 'parents'
    except KeyError:
        pass

graph.sort_nodes(attr='count', reverse=True)

gexf.write()
~~~