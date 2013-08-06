#!/usr/bin/env python
# -*- coding: utf-8 -*-

from xml.etree import ElementTree
import re


class object_dict(dict):

    def __init__(self, initd=None):
        if initd is None:
            initd = {}
        dict.__init__(self, initd)

    def __getattr__(self, item):
        d = self.__getitem__(item)
        # if value is the only key in object, you can omit it
        if isinstance(d, dict) and 'value' in d and len(d) == 1:
            return d['value']
        else:
            return d

    def __iter__(self):
        yield self
        return

    def __setattr__(self, item, value):
        self.__setitem__(item, value)


class XML2Object(object_dict):

    def __init__(self, xml):
        dom = XML2dict().fromstring(xml)
        object_dict.__init__(self, dom)


class XML2dict(object):

    def __init__(self):
        pass

    def _parse_node(self, node):
        node_tree = object_dict()
        # Save attrs and text, hope there will not be a child with same name
        if node.text:
            node_tree.value = node.text
        for (k, v) in node.attrib.items():
            k, v = self._namespace_split(k, object_dict({'value': v}))
            node_tree[k] = v
        # Save childrens
        for child in node.getchildren():
            tag, tree = self._namespace_split(
                child.tag, self._parse_node(child))
            if tag not in node_tree:  # the first time, so store it in dict
                node_tree[tag] = tree
                continue
            old = node_tree[tag]
            if not isinstance(old, list):
                node_tree.pop(tag)
                node_tree[tag] = [
                    old]  # multi times, so change old dict to a list
            node_tree[tag].append(tree)  # add the new one

        return node_tree

    def _namespace_split(self, tag, value):
        result = re.compile("\{(.*)\}(.*)").search(tag)
        if result:
            print tag
            value.namespace, tag = result.groups()
        return (tag, value)

    def parse(self, file):
        f = open(file, 'r')
        return self.fromstring(f.read())

    def fromstring(self, s):
        t = ElementTree.fromstring(s)
        root_tag, root_tree = self._namespace_split(t.tag, self._parse_node(t))
        return object_dict({root_tag: root_tree})
