"""Modification of gemfileparser to run only on provided input"""
import ast
import collections
import csv
import io
import re
from datetime import datetime


class Dependency(object):
    """
    A class to hold information about a dependency gem.
    """

    def __init__(self):
        self.name = ""
        self.requirement = []
        self.autorequire = ""
        self.source = ""
        self.parent = []
        self.group = ""

    def to_dict(self):
        """
        Return result dict
        """
        return dict(
            name=self.name,
            requirement=self.requirement,
            autorequire=self.autorequire,
            source=self.source,
            parent=self.parent,
            group=self.group,
        )


class GemfileParser(object):
    """
    Create a GemfileParser object to perform operations.
    """

    gemfile_regexes = collections.OrderedDict()
    gemfile_regexes["source"] = re.compile(r"source:[ ]?(?P<source>[a-zA-Z:\/\.-]+)")
    gemfile_regexes["git"] = re.compile(r"git:[ ]?(?P<git>[a-zA-Z:\/\.-]+)")
    gemfile_regexes["platform"] = re.compile(
        r"platform:[ ]?(?P<platform>[a-zA-Z:\/\.-]+)"
    )
    gemfile_regexes["path"] = re.compile(r"path:[ ]?(?P<path>[a-zA-Z:\/\.-]+)")
    gemfile_regexes["branch"] = re.compile(r"branch:[ ]?(?P<branch>[a-zA-Z:\/\.-]+)")
    gemfile_regexes["autorequire"] = re.compile(
        r"require:[ ]?(?P<autorequire>[a-zA-Z:\/\.-]+)"
    )
    gemfile_regexes["group"] = re.compile(r"group:[ ]?(?P<group>[a-zA-Z:\/\.-]+)")
    gemfile_regexes["name"] = re.compile(r"(?P<name>[a-zA-Z]+[\.0-9a-zA-Z _-]*)")
    gemfile_regexes["requirement"] = re.compile(
        r"(?P<requirement>([>|<|=|~>|\d]+[ ]*[0-9\.\w]+[ ,]*)+)"
    )

    group_block_regex = re.compile(r"group[ ]?:[ ]?(?P<groupblock>.*?) do")

    gemspec_add_dvtdep_regex = re.compile(r".*add_development_dependency(?P<line>.*)")
    gemspec_add_rundep_regex = re.compile(r".*add_runtime_dependency(?P<line>.*)")
    gemspec_add_dep_regex = re.compile(r".*dependency(?P<line>.*)")

    gemspec_required_ruby_version = re.compile(r".*required_ruby_version(?P<line>.*)")
    gemspec_name = re.compile(r".*name(?P<line>.*)")
    gemspec_version = re.compile(r".*version(?P<line>.*)")
    gemspec_license = re.compile(r".*license(?P<line>.*)")
    gemspec_licenses = re.compile(r".*licenses(?P<line>.*)")

    def __init__(self, content):
        self.current_group = "runtime"
        self.res = {
            "import_name": "",
            "lang_ver": [],
            "pkg_name": "",
            "pkg_ver": "",
            "pkg_lic": ["Other"],
            "pkg_err": {},
            "pkg_dep": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.dependencies = {
            "development": [],
            "runtime": [],
            "dependency": [],
            "test": [],
            "production": [],
            "metrics": [],
        }
        self.contents = content.split("\n")

    @staticmethod
    def preprocess(line):
        """
        Remove the comment portion and excess spaces.
        """

        if "#" in line:
            line = line[: line.index("#")]
        line = line.strip()
        return line

    def parse_line(self, line):
        """
        Parse a line and return a Dependency object.
        """

        # csv requires a file-like object
        linefile = io.StringIO(line)
        for line in csv.reader(linefile, delimiter=","):
            column_list = []
            for column in line:
                stripped_column = (
                    column.replace("'", "")
                    .replace('"', "")
                    .replace("%q<", "")
                    .replace("(", "")
                    .replace(")", "")
                    .replace("[", "")
                    .replace("]", "")
                    .strip()
                )
                column_list.append(stripped_column)

            dep = Dependency()
            dep.group = self.current_group
            for column in column_list:
                # Check for a match in each regex and assign to
                # corresponding variables
                for criteria, criteria_regex in GemfileParser.gemfile_regexes.items():
                    match = criteria_regex.match(column)
                    if match:
                        if criteria == "requirement":
                            dep.requirement.append(match.group(criteria))
                        else:
                            setattr(dep, criteria, match.group(criteria))
                        break
            if dep.group in self.dependencies:
                self.dependencies[dep.group].append(dep)
            else:
                self.dependencies[dep.group] = [dep]

    def handle_gemfile(self):
        """
        Parse a Gemfile
        """

        for line in self.contents:
            line = self.preprocess(line)
            if line == "" or line.startswith("source"):
                continue

            elif line.startswith("group"):
                match = self.group_block_regex.match(line)
                if match:
                    self.current_group = match.group("groupblock")

            elif line.startswith("end"):
                self.current_group = "runtime"

            elif line.startswith("gem "):
                line = line[3:]
                self.parse_line(line)

            elif line.startswith("ruby "):
                line = line[4:]
                line.replace()
        required_dep = self.dependencies.get("production", []) + self.dependencies.get(
            "dependency", []
        )
        self.res["pkg_dep"] = [d.name + ";" + d.requirement[0] for d in required_dep]
        return self.res

    def handle_gemspec(self):
        """
        Parse a .gemspec or Rakefile
        """

        for line in self.contents:
            line = self.preprocess(line)
            match = self.gemspec_add_dvtdep_regex.match(line)
            if match:
                self.current_group = "development"
            else:
                match = self.gemspec_add_rundep_regex.match(line)
                if match:
                    self.current_group = "runtime"
                else:
                    match = self.gemspec_add_dep_regex.match(line)
                    if match:
                        self.current_group = "dependency"
            if match:
                line = match.group("line")
                self.parse_line(line)
        required_dep = self.dependencies.get("production", []) + self.dependencies.get(
            "dependency", []
        )
        self.res["pkg_dep"] = [d.name + ";" + d.requirement[0] for d in required_dep]
        lang_find = self.gemspec_required_ruby_version.findall("\n".join(self.contents))
        if lang_find:
            self.res["lang_ver"] = ast.literal_eval(lang_find[0])
        lic_find = self.gemspec_license.findall("\n".join(self.contents))
        lics_find = self.gemspec_licenses.findall("\n".join(self.contents))
        if lics_find:
            self.res["pkg_lic"] = ast.literal_eval(lics_find[0])
        elif lic_find:
            self.res["pkg_lic"] = [ast.literal_eval(lic_find[0])]
        return self.res
