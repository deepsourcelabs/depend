#!/usr/bin/env python3
"""
Provides test cases for inspector.py
"""

import unittest
from inspector import *

class PythonRegistryTest(unittest.TestCase):
    """
    Test Python PyPI registry information
    """
    def test_python_pypi_registry(self):
        """ Python PyPI details """
        self.assertEqual(source['python']['registry'],   'PyPI')
        self.assertEqual(source['python']['url'],        'https://pypi.org/pypi')
        self.assertEqual(source['python']['name'],       'name')
        self.assertEqual(source['python']['version'],    'version')
        self.assertEqual(source['python']['license'],    'license')
        self.assertEqual(source['python']['dependency'], 'requires_dist')

class JavaScriptRegistryTest(unittest.TestCase):
    """
    Test JavaScript npmjs registry information
    """
    def test_python_pypi_registry(self):
        """ JavaScript npmjs details """
        self.assertEqual(source['javascript']['registry'],   'npmjs')
        self.assertEqual(source['javascript']['url'],        'https://registry.npmjs.org')
        self.assertEqual(source['javascript']['name'],       'name')
        self.assertEqual(source['javascript']['version'],    'version')
        self.assertEqual(source['javascript']['license'],    'license')
        self.assertEqual(source['javascript']['dependency'], 'dependencies')

class PythonURLTest(unittest.TestCase):
    """
    Test Python PyPI URL for package-version request
    """
    def test_python_with_version_url(self):
        """ Python PyPI URL with package version """
        self.assertEqual(make_url('python', 'aiohttp', '3.7.2'),
                         'https://pypi.org/pypi/aiohttp/3.7.2/json')

    def test_python_without_version_url(self):
        """ Python PyPI URL for latest package """
        self.assertEqual(make_url('python', 'aiohttp'),
                         'https://pypi.org/pypi/aiohttp/json')

class JavaScriptURLTest(unittest.TestCase):
    """
    Test JavaScript npmjs URL for package-version request
    """
    def test_javascript_with_version_url(self):
        """ JavaScript npmjs URL for package with version """
        self.assertEqual(make_url('javascript', 'react', '17.0.2'),
                         'https://registry.npmjs.org/react/17.0.2')

    def test_javascript_without_version_url(self):
        """ JavaScript npmjs URL for latest package version """
        self.assertEqual(make_url('javascript', 'react'),
                         'https://registry.npmjs.org/react')

class PythonRequestTest(unittest.TestCase):
    """
    Test PyPI request for single and multiple package requests
    """
    def test_make_single_request(self):
        """ Single package request to Python PyPI """
        result = make_single_request('python', 'https://pypi.org/pypi/aiohttp/3.7.2/json')
        self.assertEqual(result['name'], 'aiohttp')
        self.assertEqual(result['version'], '3.7.2')
        self.assertEqual(result['license'], 'Apache 2')
        self.assertListEqual(result['dependencies'], ['attrs (>=17.3.0)', 'chardet (<4.0,>=2.0)', 'multidict (<7.0,>=4.5)', 'async-timeout (<4.0,>=3.0)', 'yarl (<2.0,>=1.0)', 'typing-extensions (>=3.6.5)', 'idna-ssl (>=1.0) ; python_version < "3.7"', "aiodns ; extra == 'speedups'", "brotlipy ; extra == 'speedups'", "cchardet ; extra == 'speedups'"])

    def test_make_multiple_requests(self):
        """ Multiple package requests for Python PyPI """
        result = make_multiple_requests('python', ['aiohttp', 'pyxcp'])
        self.assertEqual(result['aiohttp']['license'], 'Apache 2')
        self.assertEqual(result['pyxcp']['license'], 'GPLv2')

class JavaScriptRequestTest(unittest.TestCase):
    """
    Test JavaScript npmjs requests for single and multiple package requests
    """
    def test_make_single_request(self):
        """ Single package request for JavaScript npmjs """
        result = make_single_request('javascript', 'https://registry.npmjs.org/react/17.0.2')
        self.assertEqual(result['name'], 'react')
        self.assertEqual(result['version'], '17.0.2')
        self.assertEqual(result['license'], 'MIT')
        self.assertEqual(result['dependencies'], {'loose-envify': '^1.1.0', 'object-assign': '^4.1.1'})

    def test_make_multiple_requests(self):
        """ Multiple package requests for JavaScript npmjs """
        result = make_multiple_requests('javascript', ['react', 'express'])
        self.assertEqual(result['react']['license'], 'MIT')
        self.assertEqual(result['express']['license'], 'MIT')

if __name__ == '__main__':
    unittest.main()
