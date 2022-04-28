"""Constants and config to be used by the analyzer."""
from jmespath import compile as jc

CACHE_EXPIRY = 1800.0
REGISTRY = {
    "python": {
        "registry": "PyPI",
        "url": "https://pypi.org/pypi",
        "name": jc("info.name"),
        "versions": jc("releases.keys(@)"),
        "version": jc("info.version"),
        "license": jc("info.license"),
        "dependency": jc("info.requires_dist"),
        "repo": jc("info.home_page"),
    },
    "javascript": {
        "registry": "npmjs",
        "url": "https://registry.npmjs.org",
        "name": jc("name"),
        "latest": jc('"dist-tags".latest'),
        "versions": jc("versions.keys(@)"),
        "version": jc("version"),
        "license": jc("[license,licenses|[?type!=null].type][]"),
        "dependency": jc("dependencies||__dependencies"),
        "repo": jc("homepage"),
    },
    "go": {
        "url": "https://pkg.go.dev",
        "name": "nav.go-Main-headerBreadcrumb",
        "parse": "div.go-Main-headerDetails",
        "versions": "div.Version-tag",
        "dependencies": "li.Imports-listItem",
        "version": "Version",
        "license": "License",
        "dependency": "dependencies",
    },
    "java": {
        "registry": "maven",
        "url": "https://search.maven.org/solrsearch/select?q=",
        "g": jc("response.docs[0].g"),
        "a": jc("response.docs[0].a"),
        "v": jc("response.docs[0].v"),
        "versions": jc("response.docs[*].v"),
    },
    "rust": {
        "url": "https://crates.io/api/v1/crates",
        "name": jc("version.crate"),
        "versions": jc("versions[].num"),
        "version": jc("version.num"),
        "license": jc("version.license"),
        "dependency": jc("dependencies[]|[].join(`;`, [crate_id, req])"),
    },
}
LICENSE_FILES = [
    "LICENSE",
    "LICENSE.md",
    "LICENSE.txt",
    "COPYRIGHT",
    "COPYING",
    "COPYING.md" "LICENSE.textile",
    "COPYING.textile",
    "LICENSE-MIT",
    "COPYING-MIT",
    "MIT-LICENSE-MIT",
    "MIT-COPYING",
    "OFL.md",
    "OFL.textile",
    "OFL",
    "OFL.txt",
    "PATENTS",
    "PATENTS.txt",
    "WTFPL",
    "UNLICENSE",
]
REQ_FILES = {
    "python": [
        "poetry.toml",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "requirements.txt",
        "pipfile.lock",
        "pipfile",
    ],
    "javascript": [
        "package.json",
        "package-lock.json",
        "yarn.lock",
    ],
    "go": ["go.mod"],
    "rust": [
        "Cargo.toml",
        "Cargo.lock"
    ]
}
LICENSE_DICT = {
    "AFL": "Academic Free License",
    "Apache": "Apache Software License",
    "Apple": "Apple Public Source License",
    "Artistic": "Artistic License",
    "AAL": "Attribution Assurance License",
    "Bittorrent": "Bittorrent Open Source License",
    "Boost Software License": "Boost Software License",
    "BSD 2-Clause": "BSD 2-Clause License",
    "BSD 3-Clause": "BSD 3-Clause License",
    "BSD 4-Clause": "BSD 4-Clause License",
    "BSD Zero Clause License": "BSD Zero Clause license",
    "CeCILL": "CeCILL Free Software License",
    "CDDL": "Common Development and Distribution License",
    "Creative Commons Attribution 4.0": "Creative Commons Attribution 4.0 International Public License",
    "Creative Commons Attribution-ShareAlike 4.0": "Creative Commons Attribution-ShareAlike 4.0 International Public License",
    "CC0": "Creative Commons Legal Code",
    "Clear BSD": "Clear BSD License",
    "DO WHAT THE": "Do What The F*ck You Want To Public License",
    "Eclipse Public License": "Eclipse Public License",
    "Educational Community License": "Educational Community License",
    "Eiffel": "Eiffel Forum License",
    "EUPL": "European Union Public License",
    "AGPL": "GNU Affero General Public License",
    "GNU General Public License": "GNU General Public License",
    "Lesser General Public License": "GNU Lesser General Public License",
    "HPND": "Historical Permission Notice and Disclaimer",
    "IBM Public License": "IBM Public LIcense",
    "Intel Open Source License": "Intel Open Source License",
    "ISC License": "ISC License",
    "LaTeX Project Public License": "LaTeX Project Public License",
    "Ms-PL": "Microsoft Public License",
    "Ms-RL": "Microsoft Reciprocal License",
    "MirOS": "MirOS License",
    "MIT License": "MIT License",
    "MIT No Attribution": "MIT No Attribution",
    "Mozilla Public License": "Mozilla Public License",
    "MulanPSL2": "Mulan Permissive Software License",
    "Netizen": "Netizen Open Source License",
    "Netscape Public License": "Netscape Public License",
    "Nokia Open Source License": "Nokia Open Source License",
    "ODbL": "Open Database License",
    "Open Data Commons Attribution License": "Open Data Commons Attribution License",
    "Open Software License": "Open Software License",
    "PostgreSQL License": "PostgreSQL License",
    "Python Software Foundation License": "Python Software Foundation License",
    "Python License": "Python License",
    "Public Domain": "Public Domain",
    "Q Public License": "Q Public License",
    "RealNetworks Public License": "RealNetworks Public License",
    "Repoze": "Repoze Public License",
    "SIL Open Font License": "SIL Open Font License",
    "Sleepycat": "Sleepycat License",
    "Sun Public License": "Sun Public License",
    "Watcom": "Sybase Open Watcom Public License",
    "Universal Permissive License": "Universal Permissive License",
    "NCSA": "University of Illinois/NCSA Open Source License",
    "unlicense": "Unlicense",
    "VIM LICENSE": "VIM License",
    "Vovida": "Vovida Software License",
    "W3C License": "W3C License",
    "X.Net License": "X.Net License",
    "zlib Licenqs": "zlib License",
    "Zope": "Zope Public License",
}
DEP_FIELDS_MISSED = {
    "go": {
        "mod": ["import_name", "pkg_lic"],
    },
    "javascript": {
        "json": ["import_name"],
        "lock": ["import_name", "lang_ver", "pkg_name", "pkg_ver", "pkg_lic"],
    },
    "python": {
        "py": [],
        "toml": [],
        "cfg": [],
        "txt": ["import_name", "lang_ver", "pkg_name", "pkg_ver", "pkg_lic"],
    },
}
PYPI_LIC = [
    "Aladdin Free Public License (AFPL)",
    "CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
    "CeCILL-B Free Software License Agreement (CECILL-B)",
    "CeCILL-C Free Software License Agreement (CECILL-C)",
    "DFSG approved",
    "Eiffel Forum License (EFL)",
    "Free For Educational Use",
    "Free For Home Use",
    "Free To Use But Restricted",
    "Free for non-commercial use",
    "Freely Distributable",
    "Freeware",
    "GUST Font License 1.0",
    "GUST Font License 2006-09-30",
    "Netscape Public License (NPL)",
    "Nokia Open Source License (NOKOS)",
    "OSI Approved",
    "OSI Approved :: Academic Free License (AFL)",
    "OSI Approved :: Apache Software License",
    "OSI Approved :: Apple Public Source License",
    "OSI Approved :: Artistic License",
    "OSI Approved :: Attribution Assurance License",
    "OSI Approved :: BSD License",
    "OSI Approved :: Boost Software License 1.0 (BSL-1.0)",
    "OSI Approved :: CEA CNRS Inria Logiciel Libre License, version 2.1 (CeCILL-2.1)",
    "OSI Approved :: Common Development and Distribution License 1.0 (CDDL-1.0)",
    "OSI Approved :: Common Public License",
    "OSI Approved :: Eclipse Public License 1.0 (EPL-1.0)",
    "OSI Approved :: Eclipse Public License 2.0 (EPL-2.0)",
    "OSI Approved :: Eiffel Forum License",
    "OSI Approved :: European Union Public Licence 1.0 (EUPL 1.0)",
    "OSI Approved :: European Union Public Licence 1.1 (EUPL 1.1)",
    "OSI Approved :: European Union Public Licence 1.2 (EUPL 1.2)",
    "OSI Approved :: GNU Affero General Public License v3",
    "OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
    "OSI Approved :: GNU Free Documentation License (FDL)",
    "OSI Approved :: GNU General Public License (GPL)",
    "OSI Approved :: GNU General Public License v2 (GPLv2)",
    "OSI Approved :: GNU General Public License v2 or later (GPLv2+)",
    "OSI Approved :: GNU General Public License v3 (GPLv3)",
    "OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
    "OSI Approved :: GNU Lesser General Public License v2 (LGPLv2)",
    "OSI Approved :: GNU Lesser General Public License v2 or later (LGPLv2+)",
    "OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
    "OSI Approved :: GNU Lesser General Public License v3 or later (LGPLv3+)",
    "OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
    "OSI Approved :: Historical Permission Notice and Disclaimer (HPND)",
    "OSI Approved :: IBM Public License",
    "OSI Approved :: ISC License (ISCL)",
    "OSI Approved :: Intel Open Source License",
    "OSI Approved :: Jabber Open Source License",
    "OSI Approved :: MIT License",
    "OSI Approved :: MIT No Attribution License (MIT-0)",
    "OSI Approved :: MITRE Collaborative Virtual Workspace License (CVW)",
    "OSI Approved :: MirOS License (MirOS)",
    "OSI Approved :: Motosoto License",
    "OSI Approved :: Mozilla Public License 1.0 (MPL)",
    "OSI Approved :: Mozilla Public License 1.1 (MPL 1.1)",
    "OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
    "OSI Approved :: Nethack General Public License",
    "OSI Approved :: Nokia Open Source License",
    "OSI Approved :: Open Group Test Suite License",
    "OSI Approved :: Open Software License 3.0 (OSL-3.0)",
    "OSI Approved :: PostgreSQL License",
    "OSI Approved :: Python License (CNRI Python License)",
    "OSI Approved :: Python Software Foundation License",
    "OSI Approved :: Qt Public License (QPL)",
    "OSI Approved :: Ricoh Source Code Public License",
    "OSI Approved :: SIL Open Font License 1.1 (OFL-1.1)",
    "OSI Approved :: Sleepycat License",
    "OSI Approved :: Sun Industry Standards Source License (SISSL)",
    "OSI Approved :: Sun Public License",
    "OSI Approved :: The Unlicense (Unlicense)",
    "OSI Approved :: Universal Permissive License (UPL)",
    "OSI Approved :: University of Illinois/NCSA Open Source License",
    "OSI Approved :: Vovida Software License 1.0",
    "OSI Approved :: W3C License",
    "OSI Approved :: X.Net License",
    "OSI Approved :: Zope Public License",
    "OSI Approved :: zlib/libpng License",
    "Other/Proprietary License",
    "Public Domain",
    "Repoze Public License",
]
