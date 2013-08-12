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
        return self.__getitem__(item)

    def __getitem__(self, item):
        try:
            val = dict.__getitem__(self, item)
            return val
        except:
            None

    def __iter__(self):
        yield self
        return

    def __setattr__(self, item, value):
        self.__setitem__(item, value)


class XML2Object(object_dict):

    def __init__(self, xml):
        self.dom = XML2dict().fromstring(xml)
        object_dict.__init__(self, self.dom)

def dfs(obj, name):
    lst = XMLObject()
    if isinstance(obj, dict):
        if name in obj:
            if isinstance(obj[name], list):
                lst += obj[name]
            else:
                lst.append(obj[name])
        for item in obj.values():
            lst += dfs(item, name)
    elif isinstance(obj, list):
        for item in obj:
            lst += dfs(item, name)
    return lst

class UUObject(list):
    
    def __init__(self, init = []):
        if isinstance(init,list):
            list.__init__(self, init)
        else:
            list.__init__(self, [init, ])

    def __getattr__(self, name):
        try:
            return list.__getattr__(self, name)
        except:
            try:
                if name in dir(self[0]):
                    return getattr(self[0],name)
            except:
                pass
        return self[name]

    def __getitem__(self, name):
        if isinstance(name,int):
            return list.__getitem__(self, name)
        else:
            return dfs(self,name)

    def val(self):
        if len(self)>0:
            return self[0]
        else:
            return None

    def __unicode__(self):
        if len(self)>0:
            return unicode(self[0])
        return u""
    
    def __str__(self):
        return unicode(self).encode("u8")

    def __int__(self):
        return int(str(self))

    def eq(self, index):
        if len(self)<index:
            return self[index]
        else:
            return None

    def find(self, func):
        for item in self:
            if func(item):
                return item

    def findall(self, func):
        return UUObject(filter(func, self))

class XMLObject(UUObject):

    def __init__(self, xml = None):
        if xml:
            UUObject.__init__(self,[XML2dict().fromstring(xml),])
        else:
            UUObject.__init__(self,[])

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
                    old, ]  # multi times, so change old dict to a list
            node_tree[tag].append(tree)  # add the new one
        if "value" in node_tree and len(node_tree) == 1:
            return node_tree["value"]
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

