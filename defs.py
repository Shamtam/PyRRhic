# #   Copyright (C) 2020  Shamit Som <shamitsom@gmail.com>
# #
# #   This program is free software: you can redistribute it and/or modify
# #   it under the terms of the GNU Affero General Public License as published
# #   by the Free Software Foundation, either version 3 of the License, or
# #   (at your option) any later version.
# #
# #   This program is distributed in the hope that it will be useful,
# #   but WITHOUT ANY WARRANTY; without even the implied warranty of
# #   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# #   GNU Affero General Public License for more details.
# #
# #   You should have received a copy of the GNU Affero General Public License
# #   along with this program.  If not, see <https://www.gnu.org/licenses/>.

# import logging
# import os

# from xml.etree import ElementTree as ET

# from common.definitions import ECUFlashDef
# from common.structures import Scaling, Table

# class DefinitionManager(object):
#     """Overall container for definitions"""

#     def __init__(self, rootDir=None):
#         self._ecuflash_defs = {}
#         self._logger = logging.getLogger()

#         if os.path.isdir(rootDir):
#             self.load_ecuflash_repository(rootDir)

#     def load_ecuflash_repository(self, directory):
#         """
#         Load all ECUFlash definitions stored in the given directory tree.

#         Arguments:
#          - directory: absolute path of the definition repository's top-level
#         """

#         self._ecuflash_defs = {}
#         _fpaths = {}
#         for dirname, dirs, files in os.walk(directory):
#             for f in files:

#                 # only process xml files
#                 if 'xml' not in os.path.splitext(f)[1]:
#                     continue


#                 abspath = os.path.join(dirname, f)
#                 root = ET.parse(abspath)
#                 xmlid_list = list(root.iter('xmlid'))

#                 self._logger.info(
#                     'Loading definition from file {}'.format(
#                         abspath
#                     )
#                 )

#                 if len(xmlid_list) == 1:
#                     xmlid = xmlid_list[0].text

#                     # new definition, instantiate container
#                     if xmlid not in self._ecuflash_defs:

#                         kw = {}
#                         kw['scalings'] = {}
#                         scalings = root.findall('scaling')
#                         for scaling in scalings:
#                             if {'name', 'storagetype'} <= scaling.attrib.keys():
#                                 name = scaling.attrib['name']
#                                 if name not in kw['scalings']:
#                                     kw['scalings'][name] = scaling
#                                 else:
#                                     self._logger.warn(
#                                         'Ignoring duplicate scaling {}'.format(name)
#                                     )
#                             else:
#                                 self._logger.warn(
#                                     'Ignoring insufficiently defined scaling  {}'.format(name)
#                                 )

#                         kw['parents'] = {x.text: None for x in root.findall('include')}
#                         kw['tables'] = {
#                             x.attrib['name']: x for x in root.findall('table')
#                             if 'name' in x.attrib
#                         }
#                         kw.update({x.tag: x.text for x in root.find('romid')})

#                         self._ecuflash_defs[xmlid] = ECUFlashDef(xmlid, **kw)
#                         _fpaths[xmlid] = abspath

#                     else:
#                         self._logger.warn(
#                             'Already loaded {}, skipping definition file {}'.format(
#                                 xmlid,  abspath
#                             )
#                         )
#                 else:
#                     self._logger.warn(
#                         'Malformed definition {}: multiple `xmlid`s defined'.format(
#                             abspath
#                         )
#                     )

#         for d in self._ecuflash_defs.values():
#             self._logger.info(
#                 'Resolving dependencies for definitions...'
#             )
#             try:
#                 d.resolve_dependencies(self._ecuflash_defs)
#             except Exception as e:
#                 self._logger.warn(
#                     'Malformed definition file "{}"\n{}\n'.format(
#                         _fpaths[d.Identifier], e
#                     )
#                 )
