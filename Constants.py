"""Constants and config to be used by analyzer"""
import Secrets

GITHUB_TOKEN = Secrets.GITHUB_TOKEN
CACHE_EXPIRY = 1800
DEPENDENCY_TEST = {
    'javascript':
        [
            'react@0.12.0',
            'react@17.0.2',
            'jQuery@1.7.4',
            'jQuery'
        ],
    "python":
        [
            'pygithub'
        ],
    "go":
        [
            "https://github.com/go-yaml/yaml",
            "github.com/getsentry/sentry-go",
            "github.com/cactus/go-statsd-client/v5/statsd",
        ]
}
REGISTRY = {
    'python':
        {
            'registry': 'PyPI',
            'url': 'https://pypi.org/pypi',
            'name': 'name',
            'version': 'version',
            'license': 'license',
            'dependency': 'requires_dist',
        },
    'javascript':
        {
            'registry': 'npmjs',
            'url': 'https://registry.npmjs.org',
            'name': 'name',
            'version': 'version',
            'license': 'license',
            'dependency': 'dependencies',
        },
    'go':
        {
            'url': "https://pkg.go.dev",
            'name': 'nav.go-Main-headerBreadcrumb',
            'parse': 'div.go-Main-headerDetails',
            'versions': 'div.Version-tag',
            'dependencies': 'li.Imports-listItem',
            'version': 'Version',
            'license': 'License',
            'dependency': 'dependencies',
        }
}
LICENSE_DICT = {
    'AFL': 'Academic Free License',
    'Apache': 'Apache Software License',
    'Apple': 'Apple Public Source License',
    'Artistic': 'Artistic License',
    'AAL': 'Attribution Assurance License',
    'Bittorrent': 'Bittorrent Open Source License',
    'Boost Software License': 'Boost Software License',
    'BSD 2-Clause': 'BSD 2-Clause License',
    'BSD 3-Clause': 'BSD 3-Clause License',
    'BSD 4-Clause': 'BSD 4-Clause License',
    'BSD Zero Clause License': 'BSD Zero Clause license',
    'CeCILL': 'CeCILL Free Software License',
    'CDDL': 'Common Development and Distribution License',
    'Creative Commons Attribution 4.0':
        'Creative Commons Attribution 4.0 International Public License',
    'Creative Commons Attribution-ShareAlike 4.0':
        'Creative Commons Attribution-ShareAlike 4.0 International Public License',
    'CC0': 'Creative Commons Legal Code',
    'Clear BSD': 'Clear BSD License',
    'DO WHAT THE': 'Do What The F*ck You Want To Public License',
    'Eclipse Public License': 'Eclipse Public License',
    'Educational Community License': 'Educational Community License',
    'Eiffel': 'Eiffel Forum License',
    'EUPL': 'European Union Public License',
    'AGPL': 'GNU Affero General Public License',
    'GNU General Public License': 'GNU General Public License',
    'Lesser General Public License': 'GNU Lesser General Public License',
    'HPND': 'Historical Permission Notice and Disclaimer',
    'IBM Public License': 'IBM Public LIcense',
    'Intel Open Source License': 'Intel Open Source License',
    'ISC License': 'ISC License',
    'LaTeX Project Public License': 'LaTeX Project Public License',
    'Ms-PL': 'Microsoft Public License',
    'Ms-RL': 'Microsoft Reciprocal License',
    'MirOS': 'MirOS License',
    'MIT License': 'MIT License',
    'MIT No Attribution': 'MIT No Attribution',
    'Mozilla Public License': 'Mozilla Public License',
    'MulanPSL2': 'Mulan Permissive Software License',
    'Netizen': 'Netizen Open Source License',
    'Netscape Public License': 'Netscape Public License',
    'Nokia Open Source License': 'Nokia Open Source License',
    'ODbL': 'Open Database License',
    'Open Data Commons Attribution License': 'Open Data Commons Attribution License',
    'Open Software License': 'Open Software License',
    'PostgreSQL License': 'PostgreSQL License',
    'Python Software Foundation License': 'Python Software Foundation License',
    'Python License': 'Python License',
    'Public Domain': 'Public Domain',
    'Q Public License': 'Q Public License',
    'RealNetworks Public License': 'RealNetworks Public License',
    'Repoze': 'Repoze Public License',
    'SIL Open Font License': 'SIL Open Font License',
    'Sleepycat': 'Sleepycat License',
    'Sun Public License': 'Sun Public License',
    'Watcom': 'Sybase Open Watcom Public License',
    'Universal Permissive License': 'Universal Permissive License',
    'NCSA': 'University of Illinois/NCSA Open Source License',
    'unlicense': 'Unlicense',
    'VIM LICENSE': 'VIM License',
    'Vovida': 'Vovida Software License',
    'W3C License': 'W3C License',
    'X.Net License': 'X.Net License',
    'zlib Licenqs': 'zlib License',
    'Zope': 'Zope Public License'
}
