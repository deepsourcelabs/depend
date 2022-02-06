#!/usr/bin/env python3

from github import Github

g = Github("<token>")

license_files = {"LICENSE",
		 "LICENSE.md",
		 "LICENSE.txt",
		 "COPYRIGHT",
		 "COPYING",
		 "COPYING.md"
		 "LICENSE.textile",
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
		 "UNLICENSE"
		 }

licenses = {"AFL",
	    "Apache",
	    "Apple",
	    "Artistic",
	    "AAL",
	    "Bittorrent",
	    "Boost Software License",
	    "BSD 2-Clause",
	    "BSD 3-Clause",
	    "BSD 4-Clause",
	    "BSD Zero Clause License",
	    "CeCILL",
	    "CDDL",
	    "Creative Commons Attribution 4.0",
	    "Creative Commons Attribution-ShareAlike 4.0",
	    "CC0",
	    "Clear BSD",
	    "DO WHAT THE",
	    "Eclipse Public License",
	    "Educational Community License",
	    "Eiffel",
	    "EUPL",
	    "GNU Affero General Public License",
	    "GNU General Public License",
	    "Lesser General Public License",
	    "HPND",
	    "IBM Public License",
	    "Intel Open Source License",
	    "ISC License",
	    "LaTeX Project Public License",
	    "Ms-PL",
	    "Ms-RL",
	    "MirOS",
	    "MIT License",
	    "MIT No Attribution",
	    "Mozilla Public License",
	    "MulanPSL2",
	    "Netizen",
	    "Netscape Public License",
	    "Nokia Open Source License",
	    "ODbL",
	    "Open Data Commons Attribution License",
	    "Open Software License",
	    "PostgreSQL License",
	    "Python Software Foundation License",
	    "Python License",
	    "Public Domain",
	    "Q Domain",
	    "RealNetworks Public License",
	    "Repoze",
	    "SIL Open Font License",
	    "Simplified BSD License",
	    "Sleepycat",
	    "Sun Public License",
	    "Watcom",
	    "Universal Permissive License",
	    "National Center for Supercomputing Applications",
	    "unlicense",
	    "VIM LICENSE",
	    "Vovida",
	    "W3C License",
	    "X.Net License",
	    "zlib License",
	    "Zope"}

def find_license(github_repo):
	"""
	Find license from GitHub repository
	"""
	license_filename = ""
	licence = ""
	
	repo = g.get_repo(github_repo)
	files = repo.get_contents("")
	for f in files:
		if f.name in license_files:
			license_filename = f.name

	if license_filename:
		license_contents = repo.get_contents(license_filename)
		license_text = license_contents.decoded_content.decode('utf8').split('\n')[0:25]
		for l in licenses:
			if any(l in s for s in license_text):
				licence = l
		
	return(licence)

def main():
    """
    The main function
    """
    print(find_license("kreativekorp/barcode"))

if __name__ == "__main__":
    main()



