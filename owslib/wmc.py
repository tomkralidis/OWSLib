# -*- coding: ISO-8859-15 -*-
# =============================================================================
# Copyright (c) 2004 Sean C. Gillies
# Copyright (c) 2005 Nuxeo SARL <http://nuxeo.com>
#
# Authors : Sean Gillies <sgillies@frii.com>
#           Julien Anguenot <ja@nuxeo.com>
#
# Contact email: sgillies@frii.com
# =============================================================================

"""Web Map Context (WMC)

Specification can be found over there :
https://portal.opengeospatial.org/files/?artifact_id=8618

"""

from __future__ import (absolute_import, division, print_function)

from .etree import etree

from owslib.namespaces import Namespaces

context_ns_uri = 'http://www.opengis.net/context'
context_schemas_uri = 'http://schemas.opengis.net/context/1.0.0/context.xsd'

# default variables
def get_namespaces():
    n = Namespaces()
    ns = n.get_namespaces(["context", "sld", "xlink"])
#    ns[None] = n.get_namespace("context")
    return ns
namespaces = get_namespaces()

def WMCElement(tag):
    """WMC based element
    """
    return etree.Element("{%s}"%context_ns_uri + tag)

class MapContext:
    """ Map Context abstraction

    It uses a Map representation as input and export it as as map
    context
    """

    def __init__(self, map_):
        self._map = map_

    def _getRootElement(self):
        root = WMCElement('ViewContext')
        attrs = {
            '{http://www.w3.org/2001/XMLSchema-instance}schemaLocation':
            context_ns_uri + ' ' + context_schemas_uri,
            'id' : self._map.id,
            'version' : '1.0.0',
            }
        for k, v in attrs.items():
            root.attrib[k] = v
        return root

    def _getGeneralElement(self):
        general = WMCElement('General')
        general.append(self._getWindowElement())
        general.append(self._getBoundingBoxElement())
        return general

    def _getWindowElement(self):
        window = WMCElement('Window')
        window.attrib['width'] = str(self._map.size[0])
        window.attrib['height'] = str(self._map.size[1])
        return window

    def _getBoundingBoxElement(self):
        bbox = WMCElement('BoundingBox')
        bbox.attrib['SRS'] = str(self._map.srs.split()[0])
        bbox.attrib['minx'] = str(self._map.bounds[0])
        bbox.attrib['miny'] = str(self._map.bounds[1])
        bbox.attrib['maxx'] = str(self._map.bounds[2])
        bbox.attrib['maxy'] = str(self._map.bounds[3])
        return bbox

    def _getLayerListElement(self):
        layerlist = WMCElement('LayerList')
        layering = zip(self._map.layernames, self._map.layertitles)
        layer_infos = self._map.getLayerInfos()

        # mapbuilder draws layers in bottom-top order
        for name, title in layering:

            # Layer
            layer = WMCElement('Layer')
            layer.attrib['queryable'] = '0'
            layer.attrib['hidden'] = str(
                int(name not in self._map.visible_layers))

            # Layer styles
            if layer_infos and layer_infos.get(title):
                stylelist = WMCElement('StyleList')
                # Get wms `Style` nodes for a given layer
                for e_style in layer_infos.get(title):
                    e_style.attrib['current'] = '1'
                    # Change namespace to wmc
                    for node in e_style.getiterator():
                        tag_name = node.tag[node.tag.rfind('}')+1:]
                        node.tag = "{%s}"%context_ns_uri + tag_name
                    stylelist.append(e_style)
                layer.append(stylelist)

            # Server
            server = WMCElement('Server')
            server.attrib['service'] = 'OGC:WMS'
            server.attrib['version'] = '1.1.1'
            server.attrib['title'] = 'OGC:WMS'

            # OnlineRessource
            oressource = WMCElement('OnlineResource')
            oressource.attrib[
                '{http://www.w3.org/1999/xlink}type'] = 'simple'
            oressource.attrib[
                '{http://www.w3.org/1999/xlink}href'] = self._map.url
            server.append(oressource)
            layer.append(server)

            # Name
            e_name = WMCElement('Name')
            e_name.text = name
            layer.append(e_name)

            # Title
            e_title = WMCElement('Title')
            e_title.text = title
            layer.append(e_title)

            # Format
            formatlist = WMCElement('FormatList')
            format = WMCElement('Format')
            format.attrib['current'] = '1'
            format.text = self._map.format
            formatlist.append(format)
            layer.append(formatlist)
            layerlist.append(layer)

        return layerlist

    def __call__(self):
        """Export self._map to WMC
        """
        wmc_doc_tree = self._getRootElement()
        wmc_doc_tree.append(self._getGeneralElement())
        wmc_doc_tree.append(self._getLayerListElement())
        return etree.tostring(wmc_doc_tree)


class AggregateMapContext(MapContext):
    """ Map Context abstraction

    It uses a Map representation as input and export it as as map
    context -- with aggregation of all layers accomplished through
    overload of the Layer/Name property
    """

    def _getLayerListElement(self):
        layerlist = WMCElement('LayerList')
        #layering = zip(self._map.layernames, self._map.layertitles)
        layer_infos = self._map.getLayerInfos()

        # Layer
        layer = WMCElement('Layer')
        layer.attrib['queryable'] = '0'
        layer.attrib['hidden'] = '0'

        # Server
        server = WMCElement('Server')
        server.attrib['service'] = 'OGC:WMS'
        server.attrib['version'] = '1.1.1'
        server.attrib['title'] = 'OGC:WMS'

        # OnlineRessource
        oressource = WMCElement('OnlineResource')
        oressource.attrib['{http://www.w3.org/1999/xlink}type'] = 'simple'
        oressource.attrib['{http://www.w3.org/1999/xlink}href'] = self._map.url
        server.append(oressource)
        layer.append(server)

        # Name
        e_name = WMCElement('Name')
        e_name.text = ','.join(self._map.layernames)
        layer.append(e_name)

        # Title
        e_title = WMCElement('Title')
        e_title.text = 'Aggregate Layers'
        layer.append(e_title)

        # Format
        formatlist = WMCElement('FormatList')
        format = WMCElement('Format')
        format.attrib['current'] = '1'
        format.text = self._map.format
        formatlist.append(format)
        layer.append(formatlist)
        layerlist.append(layer)
        
        return layerlist


def mapToWebMapContext(map, aggregate_layers=False):
    """Helper

    if the second argument evaluates to True, then all map layers are
    aggregated into a single map context layer.
    """
    if aggregate_layers:
        return AggregateMapContext(map)()
    else:
        return MapContext(map)()


class ViewContext(object):
    """WMC Context 1.0.0 parser"""

    def __init__(self, exml=None):
        """init"""

        self.id = None
        self.version = None
        self.layerlist = []
        self.general = General()

        if exml is None:
            return

        self._exml = exml.getroot()

        self.id = self._exml.attrib.get('id')
        self.version = self._exml.attrib.get('version')

        self.general = General(self._exml.find('{http://www.opengis.net/context}General'))

        for layer in self._exml.findall('{http://www.opengis.net/context}LayerList/{http://www.opengis.net/context}Layer'):
            self.layerlist.append(Layer(layer))

    def dumps(self):
        """write context:ViewContext etree object"""

        if etree.__name__ == 'lxml.etree':  # apply nsmap
            viewcontext = etree.Element('{http://www.opengis.net/context}ViewContext', nsmap=namespaces)
        else:
            viewcontext = etree.Element('{http://www.opengis.net/context}ViewContext')

        viewcontext.attrib['version'] = self.version or '1.1.0'
        viewcontext.attrib['id'] = self.id or 'owslib-wmc'

        viewcontext.append(self.general.toexml())

        if self.layerlist:
            layerlist = etree.SubElement(viewcontext, '{http://www.opengis.net/context}LayerList')
            for layer in self.layerlist:
                layerlist.append(layer.toexml())

        return etree.tostring(viewcontext)

    def __repr__(self):
        """representation"""
        return '<ViewContext %r>' % self.general.title

class General(object):
    """General"""

    def __init__(self, el=None):
        """init"""

        self.el = el
        self.window = Window()
        self.bbox = BoundingBox()
        self.title = None
        self.keywords = []
        self.abstract = None
        self.logourl = URLType()
        self.descriptionurl = URLType()
        self.contact = ContactInformation()

        if self.el is None:
            return

        self.window = Window(self.el.find('{http://www.opengis.net/context}Window'))
        self.bbox = BoundingBox(self.el.find('{http://www.opengis.net/context}BoundingBox'))

        value = self.el.find('{http://www.opengis.net/context}Title')
        if value is not None:
            self.title = value.text

        self.keywords = []
        for keyword in self.el.findall('{http://www.opengis.net/context}KeywordList/{http://www.opengis.net/context}Keyword'):
            self.keywords.append(keyword.text)

        value = self.el.find('{http://www.opengis.net/context}Abstract')
        if value is not None:
            self.abstract = value.text

        value = self.el.find('{http://www.opengis.net/context}LogoURL')
        if value is not None:
            self.logourl = URLType(value)

        value = self.el.find('{http://www.opengis.net/context}DescriptionURL')
        if value is not None:
            self.descriptionurl = URLType(value)

        value = self.el.find('{http://www.opengis.net/context}ContactInformation')
        if value is not None:
            self.contact = ContactInformation(value)

    def toexml(self):
        """serialize to etree.Element"""

        general = etree.Element(self.el.tag)

        if self.window is not None:
            general.append(self.window.toexml())
        if self.bbox is not None:
            general.append(self.bbox.toexml())
        if self.title is not None:
            etree.SubElement(general, '{http://www.opengis.net/context}Title').text = self.title
        if self.keywords:
            kws = etree.SubElement(general, '{http://www.opengis.net/context}KeywordList')
            for keyword in self.keywords:
                etree.SubElement(kws, '{http://www.opengis.net/context}Keyword').text = keyword
        if self.abstract is not None:
            etree.SubElement(general, '{http://www.opengis.net/context}Abstract').text = self.abstract
        if self.logourl is not None:
            general.append(self.logourl.toexml())
        if self.descriptionurl is not None:
            general.append(self.descriptionurl.toexml())
        if self.contact is not None:
            general.append(self.contact.toexml())

        return general


class Window(object):
    """Window"""

    def __init__(self, el=None):
        """init"""

        self.el = el
        self.width = None
        self.height = None

        if self.el is None:
            return

        self.width = self.el.attrib.get('width')
        self.height = self.el.attrib.get('height')

    def toexml(self):
        """serialize to etree.Element"""

        window = etree.Element(self.el.tag)

        if self.width is not None:
            window.attrib['width'] = self.width
        if self.height is not None:
            window.attrib['height'] = self.height

        return window


class BoundingBox(object):
    """BoundingBox"""

    def __init__(self, el=None):
        """init"""

        self.el = el
        self.srs = None
        self.minx = None
        self.miny = None
        self.maxx = None
        self.maxy = None

        if el is None:
            return

        self.srs = el.attrib.get('SRS')
        self.minx = el.attrib.get('minx')
        self.miny = el.attrib.get('miny')
        self.maxx = el.attrib.get('maxx')
        self.maxy = el.attrib.get('maxy')

    def toexml(self):
        """serialize to etree.Element"""

        bbox = etree.Element(self.el.tag)

        if self.srs is not None:
            bbox.attrib['SRS'] = self.srs
        if self.minx is not None:
            bbox.attrib['minx'] = self.minx
        if self.miny is not None:
            bbox.attrib['miny'] = self.miny
        if self.maxx is not None:
            bbox.attrib['maxx'] = self.maxx
        if self.maxy is not None:
            bbox.attrib['maxy'] = self.maxy

        return bbox


class ContactInformation(object):
    """ContactInformation"""

    def __init__(self, el=None):
        """init"""

        self.el = el
        self.person = None
        self.organization = None
        self.position = None
        self.address = Address()
        self.telephone = None
        self.fax = None
        self.email = None

        if self.el is None:
            return

        value = self.el.find('{http://www.opengis.net/context}ContactPersonPrimary/{http://www.opengis.net/context}ContactPerson')
        if value is not None:
            self.person = value.text

        value = self.el.find('{http://www.opengis.net/context}ContactPersonPrimary/{http://www.opengis.net/context}ContactOrganization')
        if value is not None:
            self.organization = value.text

        value = self.el.find('{http://www.opengis.net/context}ContactPosition')
        if value is not None:
            self.position = value.text

        value = self.el.find('{http://www.opengis.net/context}ContactAddress')
        if value is not None:
            self.address = Address(value)

        value = self.el.find('{http://www.opengis.net/context}ContactVoiceTelephone')
        if value is not None:
            self.telephone = value.text

        value = self.el.find('{http://www.opengis.net/context}ContactFacsimileTelephone')
        if value is not None:
            self.fax = value.text

        value = self.el.find('{http://www.opengis.net/context}ContactElectronicMailAddress')
        if value is not None:
            self.email = value.text

    def toexml(self):
        """serialize to etree.Element"""

        ci = etree.Element(self.el.tag)

        if self.person is not None or self.organization is not None:
            cpp = etree.SubElement(ci, '{http://www.opengis.net/context}ContactPersonPrimary')
            if self.person is not None:
                etree.SubElement(cpp, '{http://www.opengis.net/context}ContactPerson').text = self.person
            if self.organization is not None:
                etree.SubElement(cpp, '{http://www.opengis.net/context}ContactOrganization').text = self.organization
        if self.position is not None:
            etree.SubElement(ci, '{http://www.opengis.net/context}ContactPosition').text = self.position
        if self.address is not None:
            ci.append(self.address.toexml())
        if self.telephone is not None:
            etree.SubElement(ci, '{http://www.opengis.net/context}ContactVoiceTelephone').text = self.telephone
        if self.fax is not None:
            etree.SubElement(ci, '{http://www.opengis.net/context}ContactFacsimileTelephone').text = self.fax
        if self.email is not None:
            etree.SubElement(ci, '{http://www.opengis.net/context}ContactElectronicMailAddress').text = self.email

        return ci


class Address(object):
    """Address"""

    def __init__(self, el=None):
        """init"""

        self.el = el
        self.addresstype = None
        self.address = None
        self.city = None
        self.stateorprovince = None
        self.postcode = None
        self.country = None

        if self.el is None:
            return

        value = self.el.find('{http://www.opengis.net/context}AddressType')
        if value is not None:
            self.addresstype = value.text

        value = self.el.find('{http://www.opengis.net/context}Address')
        if value is not None:
            self.address = value.text
        
        value = self.el.find('{http://www.opengis.net/context}City')
        if value is not None:
            self.city = value.text

        value = self.el.find('{http://www.opengis.net/context}StateOrProvince')
        if value is not None:
            self.stateorprovince = value.text

        value = self.el.find('{http://www.opengis.net/context}PostCode')
        if value is not None:
            self.postcode = value.text

        value = self.el.find('{http://www.opengis.net/context}Country')
        if value is not None:
            self.country = value.text

    def toexml(self):
        """serialize to etree.Element"""

        address = etree.Element(self.el.tag)

        if self.addresstype is not None:
            etree.SubElement(address, '{http://www.opengis.net/context}AddressType').text = self.addresstype
        if self.address is not None:
            etree.SubElement(address, '{http://www.opengis.net/context}Address').text = self.address
        if self.city is not None:
            etree.SubElement(address, '{http://www.opengis.net/context}City').text = self.city
        if self.stateorprovince is not None:
            etree.SubElement(address, '{http://www.opengis.net/context}StateOrProvince').text = self.stateorprovince
        if self.postcode is not None:
            etree.SubElement(address, '{http://www.opengis.net/context}PostCode').text = self.postcode
        if self.country is not None:
            etree.SubElement(address, '{http://www.opengis.net/context}Country').text = self.country

        return address


class URLType(object):
    """URLType"""

    def __init__(self, el=None):
        """init"""

        self.el = el
        self.width = None
        self.height = None
        self.format = None
        self.url = None

        if self.el is None:
            return

        self.width = self.el.attrib.get('width')
        self.height = self.el.attrib.get('height')
        self.format = self.el.attrib.get('format')

        value = self.el.find('{http://www.opengis.net/context}OnlineResource')
        if value is not None:
            self.url = value.attrib.get('{http://www.w3.org/1999/xlink}href')

    def toexml(self):
        """serialize to etree.Element"""

        url = etree.Element(self.el.tag)

        if self.width is not None:
            url.attrib['width'] = self.width
        if self.height is not None:
            url.attrib['height'] = self.height
        if self.format is not None:
            url.attrib['format'] = self.format
        if self.url is not None:
            or_ = etree.SubElement(url, '{http://www.opengis.net/context}OnlineResource')
            or_.attrib['{http://www.w3.org/1999/xlink}href'] = self.url

        return url


    def __repr__(self):
        """representation"""
        return '<URLType %r %r>' % (self.el.tag, self.url)

class Layer(object):
    """Layer"""

    def __init__(self, el=None):
        """init"""

        self.el = el
        self.queryable = None
        self.hidden = None
        self.server = {}
        self.name = None
        self.title = None
        self.abstract = None
        self.dataurl = URLType()
        self.metadataurl = URLType()
        self.minscale = None
        self.maxscale = None
        self.srslist = []
        self.formats = []
        self.styles = []
        self.dimensions = []

        if self.el is None:
            return

        self.queryable = self.el.attrib.get('queryable')
        self.hidden = self.el.attrib.get('hidden')

        server = self.el.find('{http://www.opengis.net/context}Server')

        self.server['service'] = server.attrib.get('service')
        self.server['version'] = server.attrib.get('version')
        self.server['title'] = server.attrib.get('title')
        self.server['url'] = server.find('{http://www.opengis.net/context}OnlineResource').attrib.get('{http://www.w3.org/1999/xlink}href')

        self.name = self.el.find('{http://www.opengis.net/context}Name').text
        self.title = self.el.find('{http://www.opengis.net/context}Title').text

        value = self.el.find('{http://www.opengis.net/context}Abstract')
        if value is not None:
            self.abstract = value.text

        value = self.el.find('{http://www.opengis.net/context}DataURL')
        if value is not None:
            self.dataurl = URLType(value)

        value = self.el.find('{http://www.opengis.net/context}MetadataURL')
        if value is not None:
            self.metadataurl = URLType(value)

        value = self.el.find('{http://www.opengis.net/sld}MinScaleDenominator')
        if value is not None:
            self.minscale = URLType(value)

        value = self.el.find('{http://www.opengis.net/sld}MaxScaleDenominator')
        if value is not None:
            self.maxscale = URLType(value)

        for srs in self.el.findall('{http://www.opengis.net/context}SRS'):
            self.srslist.append(srs.text)

        for format_ in self.el.findall('{http://www.opengis.net/context}FormatList/{http://www.opengis.net/context}Format'):
            self.formats.append({'name': format_.text, 'current': format_.attrib.get('current')})

        for style in self.el.findall('{http://www.opengis.net/context}StyleList/{http://www.opengis.net/context}Style'):
            style_ = {}
            style_['current'] = style.attrib.get('current')
            style_['name'] = style.find('{http://www.opengis.net/context}Name').text
            style_['title'] = style.find('{http://www.opengis.net/context}Title').text

            value = style.find('{http://www.opengis.net/context}Abstract')
            if value is not None:
                style_['abstract'] = value.text

            value = style.find('{http://www.opengis.net/context}LegendURL')
            if value is not None:
                style_['legendurl'] = URLType(value)

            self.styles.append(style_)

        for dimension in self.el.findall('{http://www.opengis.net/context}DimensionList/{http://www.opengis.net/context}Dimension'):
            dimension_ = []
            dimension_['name'] = dimension.attrib.get('name')
            dimension_['units'] = dimension.attrib.get('units')
            dimension_['unitsymbol'] = dimension.attrib.get('unitSymbol')
            dimension_['userValue'] = dimension.attrib.get('userValue')
            dimension_['default'] = dimension.attrib.get('default')
            dimension_['multiplevalues'] = dimension.attrib.get('multipleValues')
            dimension_['nearestvalue'] = dimension.attrib.get('nearestValue')
            dimension_['current'] = dimension.attrib.get('current')

            self.dimensions.append(dimension_)

    def toexml(self):
        """serialize to etree.Element"""

        layer = etree.Element(self.el.tag)

        layer.attrib['queryable'] = self.queryable or '0'
        layer.attrib['hidden'] = self.hidden or '0'

        server = etree.SubElement(layer, '{http://www.opengis.net/context}Server', service=self.server['service'], version=self.server['version'], title=self.server['title'])
        or_ = etree.SubElement(server, '{http://www.opengis.net/context}OnlineResource')
        or_.attrib['{http://www.w3.org/1999/xlink}type'] = 'simple'
        or_.attrib['{http://www.w3.org/1999/xlink}href'] = self.server['url']

        etree.SubElement(layer, '{http://www.opengis.net/context}Name').text = self.name
        etree.SubElement(layer, '{http://www.opengis.net/context}Title').text = self.title

        return layer


    def __repr__(self):
        """representation"""
        return '<Layer %r>' % self.name
