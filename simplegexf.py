import os
from collections import OrderedDict, MutableMapping, MutableSequence
from operator import itemgetter, attrgetter
from copy import deepcopy

import xmltodict


TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<gexf xmlns="http://www.gexf.net/1.2draft"
      xmlns:viz="http://www.gexf.net/1.1draft/viz"
      xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
      xsi:schemaLocation="http://www.gexf.net/1.2draft http://www.gexf.net/1.2draft/gexf.xsd"
      version="1.2"
></gexf>"""


class BaseElement:
    def __init__(self, parent, data):
        self.parent = parent
        self.data = data or OrderedDict()

    def set(self, name, _text=None, **kwargs):
        element = OrderedDict([('@%s' % k, str(kwargs[k])) for k in sorted(kwargs)])
        if _text:
            element['#text'] = _text
        self.data[name] = element
        return element

    def _mklst(self, tag, **kwargs):
        try:
            el = self.data['%ss' % tag]
            if type(el[tag]).__name__ != 'list':
                el[tag] = [el[tag]]
        except (KeyError, TypeError):
            el = self.set('%ss' % tag, **kwargs)
            el[tag] = []
        return el

    def get(self, name, default=None):
        return self.data.get(name, default)

    def __getattribute__(self, attr):
        try:
            return super().__getattribute__(attr)
        except AttributeError:
            try:
                return self.data['@%s' % attr]
            except KeyError:
                raise AttributeError(attr)

    def __getitem__(self, key):
        return self.data[key]

    def __setitem__(self, key, value):
        self.data['key'] = value

    def __delitem__(self, key):
        del self.data['key']


class Gexf(BaseElement):
    def __init__(self, path):
        self.path = os.path.realpath(path)

        try:
            xml = open(self.path, 'r', encoding='utf-8').read()
        except IOError:
            xml = TEMPLATE

        self.tree = xmltodict.parse(xml)

        self._mklst('graph')

    @property
    def data(self):
        return self.tree['gexf']

    @data.setter
    def data(self, value):
        self.tree['gexf'] = value

    def write(self):
        open(self.path, 'w+', encoding='utf-8').write(str(self))

    @property
    def _graphs(self):
        return self.data['graphs']['graph']

    @property
    def graphs(self):
        return [Graph(self, graph) for graph in self._graphs]

    def add_graph(self, **kwargs):
        el = OrderedDict([('@%s' % k, str(kwargs[k])) for k in sorted(kwargs)])
        self._graphs.append(el)
        return Graph(self, el)

    @property
    def clean_tree(self):
        # TODO: Remove all empty lists.
        return self.tree

    def __str__(self):
        return xmltodict.unparse(self.clean_tree, pretty=True)


# class GexfGraphs(MutableSequence):


class Graph(BaseElement):
    def __init__(self, *args):
        super().__init__(*args)

        try:
            attr_wrapper_list = self.data['attributes']

            # Ensure `attr_wrapper_list` is a list:
            if type(attr_wrapper_list).__name__ != 'list':
                self.data['attributes'] = [self.data['attributes']]
                attr_wrapper_list = self.data['attributes']

        except (KeyError, TypeError):
            attr_wrapper_list = []
            self.data['attributes'] = attr_wrapper_list

        for _class in ['node', 'edge']:
            try:
                [attr_wrapper] = filter(lambda x: x['@class'] == _class,
                                      attr_wrapper_list)
            except ValueError:
                attr_wrapper = OrderedDict([
                    ('@class', _class),
                    ('attribute', [])
                ])
                attr_wrapper_list.append(attr_wrapper)

            # If there is only one attribute in the parsed data,
            # it will not be a list, so we need to fix that:
            if type(attr_wrapper['attribute']).__name__ != 'list':
                attr_wrapper['attribute'] = [attr_wrapper['attribute']]

        self._mklst('node')
        self._mklst('edge')

        self.edges = GraphEdges(self)

    @property
    def _nodes(self):
        return self.data['nodes']['node']

    @_nodes.setter
    def _nodes(self, value):
        self.data['nodes']['node'] = value

    @property
    def _edges(self):
        return self.data['edges']['edge']

    @_edges.setter
    def _edges(self, value):
        self.data['edges']['edge'] = value

    @property
    def nodes(self):
        return [Node(self, node) for node in self._nodes]

    def add_node(self, **kwargs):
        el = OrderedDict([('@%s' % k, str(kwargs[k])) for k in sorted(kwargs)])
        self._nodes.append(el)
        return Node(self, el)

    def sort_nodes(self, key=None, attr=None, type_cast=int, reverse=False):
        if key:
            _key = key
        elif attr:
            _key = lambda x: type_cast(x.attributes[attr])

        self._nodes = list(map(attrgetter('data'),
                           sorted(self.nodes, key=_key, reverse=reverse)))

    @property
    def _class_mapped_attributes(self):
        return {w['@class']: w['attribute'] for w in self.data['attributes']}

    def get_id_mapped_attributes(self, _class):
        return {int(attr['@id']): {
            'title': attr['@title'],
            'type': attr['@type']
        } for attr in self._class_mapped_attributes[_class]}

    def get_attributes(self, _class):
        return OrderedDict([(attr['@title'], {
            'id': int(attr['@id']),
            'type': attr['@type']
        }) for attr in self._class_mapped_attributes[_class]])

    @property
    def node_attributes(self):
        return self.get_attributes('node')

    @property
    def edge_attributes(self):
        return self.get_attributes('edge')

    def define_attributes(self, attributes, _class='node'):
        defined = self.get_attributes(_class).keys()
        _attributes = self._class_mapped_attributes[_class]

        for attr, _type in attributes:
            if attr in defined:
                continue

            el = OrderedDict([
                ('@id', str(len(_attributes))),
                ('@title', str(attr)),
                ('@type', str(_type))
            ])

            _attributes.append(el)


class GraphEdges(MutableSequence):
    def __init__(self, graph):
        self.graph = graph

    def __getitem__(self, index):
        edge = Edge(None, None)
        edge.data = self.graph._edges[index]
        edge._create_attributes(self.graph)
        return edge

    def __setitem__(self, index, edge):
        self.graph._edges[index] = edge.data

    def __delitem__(self, index):
        del self.graph._edges[index]

    def __len__(self):
        return len(self.graph._edges)

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return "<GraphEdges %s>" % self.graph.edges

    def insert(self, index, edge):
        edge._create_attributes(self.graph)

        # No duplicates:
        if edge in self.graph.edges:
            return

        self.graph._edges.insert(index, edge.data)

        for i, el in enumerate(self.graph._edges):
            el['@id'] = str(i)

    def append(self, edge):
        self.insert(len(self.graph._edges), edge)


class Edge(BaseElement):
    def __init__(self, source, target, id=None, type=None):
        self.data = OrderedDict([
            ('@id', str(id)),
            ('@source', str(source)),
            ('@target', str(target))
        ])

        if type:
            self.data['@type'] = str(type)

        self._mklst('attvalue')

    def _create_attributes(self, graph):
        self._attributes = EdgeAttributes(graph, self)

    @property
    def attributes(self):
        try:
            return self._attributes
        except AttributeError:
            raise AttributeError('Attributes are not available before edge '
                                 'has been added to a graph')

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return '<Node %s -> %s>' % (self.source, self.target)

    def __eq__(self, other):
        return str(self) == str(other)


class Node(BaseElement):
    def __init__(self, *args):
        super().__init__(*args)
        self._mklst('attvalue')
        self.attributes = NodeAttributes(self.parent, self)


class NodeAttributes(MutableMapping):
    _class = 'node'

    def __init__(self, graph, obj, *args, **kwargs):
        self.graph = graph
        self.obj = obj
        self.update(dict(*args, **kwargs))

    @property
    def _attvalues(self):
        return self.obj.data['attvalues']['attvalue']

    @property
    def _mapped_attvalues(self):
        return {int(v['@for']): v for v in self._attvalues}

    def __getitem__(self, key):
        tkey = self.__keytransform__(key)
        return self._mapped_attvalues[tkey]['@value']

    def __setitem__(self, key, value):
        tkey = self.__keytransform__(key)

        _value = str(value)

        if self.graph.get_attributes(self._class)[key]['type'] == 'boolean':
            _value = _value.lower()

        try:
            self._mapped_attvalues[tkey]['@value'] = _value
        except KeyError:
            # Create a new <attvalue/> element:
            # XML Output:
            #  <attvalue for="<tkey>" value="<value>"></attvalue>
            el = OrderedDict([('@for', str(tkey)), ('@value', _value)])
            self._attvalues.append(el)

    def __delitem__(self, key):
        # Should not have to find the actual index as the id should be the
        # same as the index:
        tkey = self.__keytransform__(key)
        del self._attvalues[tkey]

    def __iter__(self):
        return iter(map(lambda id: self.graph.get_id_mapped_attributes(self._class)[id]['title'],
                        self._mapped_attvalues.keys()))

    def __len__(self):
        return len(self._attvalues)

    def __keytransform__(self, key):
        return int(self.graph.get_attributes(self._class)[key]['id'])


class EdgeAttributes(NodeAttributes):
    _class = 'edge'
