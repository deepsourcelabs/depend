#!/usr/bin/env python3
"""
Provides test cases for inspector.py
"""

import unittest
from licence import *

class LicenceIdentifyTest(unittest.TestCase):
	"""
	Test valid license identification
	"""
	def test_find_license_registry(self):
		""" Valid licenses """
		self.assertEqual(find_license("apache/mesos"), 'Apache')
		self.assertEqual(find_license("kmike/text-unidecode"), 'Artistic')
		self.assertEqual(find_license("codegrafix/dlib-cpp"), 'Boost Software License')
		self.assertEqual(find_license("4creators/jxrlib"), 'BSD 2-Clause')
		self.assertEqual(find_license("r0kk3rz/bsd-3-clause"), 'BSD 3-Clause')
		self.assertEqual(find_license("input-output-hk/Scorex"), 'CC0')
		self.assertEqual(find_license("fzi-forschungszentrum-informatik/oadrive"), 'CDDL')
		self.assertEqual(find_license("FreeBiblesIndia/Punjabi_Bible"), 'Creative Commons Attribution-ShareAlike 4.0')
		self.assertEqual(find_license("jslicense/WTFPL"), 'DO WHAT THE')
		self.assertEqual(find_license("kamilla/jambot"), 'Eiffel')
		self.assertEqual(find_license("nickkoza/ironVoxel"), 'GNU General Public License')
		self.assertEqual(find_license("jonrandoem/eyeos"), 'GNU Affero General Public License')
		self.assertEqual(find_license("kreativekorp/barcode"), 'MIT License')
		self.assertEqual(find_license("FunPanda08/Web-browser"), 'Mozilla Public License')
		self.assertEqual(find_license("alandipert/ncsa-mosaic"), 'National Center for Supercomputing Applications')
		self.assertEqual(find_license("SorkinType/Basic"), 'SIL Open Font License')
		self.assertEqual(find_license("prepare/opendiagram"), 'Simplified BSD License')
		self.assertEqual(find_license("Wolfgang-Spraul/fpgatools"), 'unlicense')
		self.assertEqual(find_license("Pylons/waitress"), 'Zope')
		self.assertEqual(find_license("superzazu/SDL_nmix"), 'zlib License')

if __name__ == '__main__':
    unittest.main()
