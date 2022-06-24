"""Helper for Lax Semantic Versioning"""
from __future__ import print_function

import collections
import re
from functools import wraps

string_types = str, bytes
text_type = str
binary_type = bytes


def char_last(string):
    """Separates non numeric characters"""
    hold = ["0", "0", "0"]
    channel = ["", "", ""]
    dot_count = 0
    fall_through = False
    for c in string:
        if c.isdigit() and not fall_through:
            if hold[dot_count] == "0":
                hold[dot_count] = str(c)
            else:
                hold[dot_count] += str(c)
        elif c == "." and dot_count < 2:
            dot_count += 1
            fall_through = False
        elif c != ".":
            channel[dot_count] = channel[dot_count] + c
            fall_through = True
    return hold, "".join(channel)


def fix_ver(ver):
    """Returns semver compliant version number"""
    ver_c = ver.split("-")
    if len(ver_c) > 1:
        channel = ver_c[1]
    else:
        channel = ""
    ver_fix, false_channel = char_last(ver_c[0])
    if channel or false_channel:
        return ".".join(ver_fix[0:3]) + "-" + false_channel + channel
    else:
        return ".".join(ver_fix[0:3])


def cmp(a, b):
    """Return negative if a<b, zero if a==b, positive if a>b."""
    return (a > b) - (a < b)


def _nat_cmp(a, b):
    def convert(text):
        """
        Convert each subpart to int if its a whole number
        """
        return int(text) if re.match("^[0-9]+$", text) else text

    def split_key(key):
        """
        Split at the . character
        """
        return [convert(c) for c in key.split(".")]

    def cmp_prerelease_tag(a1, b1):
        """Compare Pre-release tags"""
        if isinstance(a1, int) and isinstance(b1, int):
            return cmp(a1, b1)
        elif isinstance(a1, int):
            return -1
        elif isinstance(b1, int):
            return 1
        else:
            return cmp(a1, b1)

    a, b = a or "", b or ""
    a_parts, b_parts = split_key(a), split_key(b)
    for sub_a, sub_b in zip(a_parts, b_parts):
        cmp_result = cmp_prerelease_tag(sub_a, sub_b)
        if cmp_result != 0:
            return cmp_result
    else:
        return cmp(len(a), len(b))


def comparator(operator):
    """Wrap a VersionInfo binary op method in a type-check."""

    @wraps(operator)
    def wrapper(self, other):
        """Type check"""
        comparable_types = (VersionInfo, dict, tuple, list, text_type, binary_type)
        if not isinstance(other, comparable_types):
            raise TypeError(
                "other type %r must be in %r" % (type(other), comparable_types)
            )
        return operator(self, other)

    return wrapper


def fakeint(param) -> int:
    """Returns a number for string passed in"""
    return sum([ord(i) for i in param])


class VersionInfo(object):
    """
    A semver compatible version class.

    :param int major: version when you make incompatible API changes.
    :param int minor: version when you add functionality in
                      a backwards-compatible manner.
    :param int patch: version when you make backwards-compatible bug fixes.
    :param str prerelease: an optional prerelease string
    :param str build: an optional build string
    """

    __slots__ = ("_major", "_minor", "_patch", "_prerelease", "_build")
    #: Regex for number in a prerelease
    _LAST_NUMBER = re.compile(r"(?:[^\d]*(\d+)[^\d]*)+")
    #: Regex for a semver version
    _REGEX = re.compile(
        r"""
            ^
            (?P<major>\w+)
            \.
            (?P<minor>\w+)
            \.
            (?P<patch>\w+)
            (?:-(?P<prerelease>
                (?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)
                (?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*
            ))?
            (?:\+(?P<build>
                [0-9a-zA-Z-]+
                (?:\.[0-9a-zA-Z-]+)*
            ))?
            $
        """,
        re.VERBOSE,
    )

    def __init__(self, major, minor=0, patch=0, prerelease=None, build=None):
        # Build a dictionary of the arguments except prerelease and build
        version_parts = {
            "major": major,
            "minor": minor,
            "patch": patch,
        }

        for name, value in version_parts.items():
            value = int(value)
            version_parts[name] = value
            if value < 0:
                raise ValueError(
                    "{!r} is negative. A version can only be positive.".format(name)
                )

        self._major = version_parts["major"]
        self._minor = version_parts["minor"]
        self._patch = version_parts["patch"]
        self._prerelease = None if prerelease is None else str(prerelease)
        self._build = None if build is None else str(build)

    @property
    def major(self):
        """The major part of a version (read-only)."""
        return self._major

    @major.setter
    def major(self, value):
        raise AttributeError("attribute 'major' is readonly")

    @property
    def minor(self):
        """The minor part of a version (read-only)."""
        return self._minor

    @minor.setter
    def minor(self, value):
        raise AttributeError("attribute 'minor' is readonly")

    @property
    def patch(self):
        """The patch part of a version (read-only)."""
        return self._patch

    @patch.setter
    def patch(self, value):
        raise AttributeError("attribute 'patch' is readonly")

    @property
    def prerelease(self):
        """The prerelease part of a version (read-only)."""
        return self._prerelease

    @prerelease.setter
    def prerelease(self, value):
        raise AttributeError("attribute 'prerelease' is readonly")

    @property
    def build(self):
        """The build part of a version (read-only)."""
        return self._build

    @build.setter
    def build(self, value):
        raise AttributeError("attribute 'build' is readonly")

    def to_tuple(self):
        """
        Convert the VersionInfo object to a tuple.

        .. versionadded:: 2.10.0
           Renamed ``VersionInfo._astuple`` to ``VersionInfo.to_tuple`` to
           make this function available in the public API.

        :return: a tuple with all the parts
        :rtype: tuple

        semver.VersionInfo(5, 3, 1).to_tuple()
        (5, 3, 1, None, None)
        """
        return self.major, self.minor, self.patch, self.prerelease, self.build

    def to_dict(self):
        """
        Convert the VersionInfo object to an OrderedDict.

        .. versionadded:: 2.10.0
           Renamed ``VersionInfo._asdict`` to ``VersionInfo.to_dict`` to
           make this function available in the public API.

        :return: an OrderedDict with the keys in the order ``major``, ``minor``,
          ``patch``, ``prerelease``, and ``build``.
        :rtype: :class:`collections.OrderedDict`

        semver.VersionInfo(3, 2, 1).to_dict()
        OrderedDict([('major', 3), ('minor', 2), ('patch', 1), \
('prerelease', None), ('build', None)])
        """
        return collections.OrderedDict(
            (
                ("major", self.major),
                ("minor", self.minor),
                ("patch", self.patch),
                ("prerelease", self.prerelease),
                ("build", self.build),
            )
        )

    def __iter__(self):
        """Implement iter(self)."""
        # As long as we support Py2.7, we can't use the "yield from" syntax
        for v in self.to_tuple():
            yield v

    @staticmethod
    def _increment_string(string):
        """
        Look for the last sequence of number(s) in a string and increment.

        :param str string: the string to search for.
        :return: the incremented string

        Source:
        http://code.activestate.com/recipes/442460-increment-numbers-in-a-string/#c1
        """
        match = VersionInfo._LAST_NUMBER.search(string)
        if match:
            next_ = str(int(match.group(1)) + 1)
            start, end = match.span(1)
            string = string[: max(end - len(next_), start)] + next_ + string[end:]
        return string

    def bump_major(self):
        """
        Raise the major part of the version, return a new object but leave self
        untouched.

        :return: new object with the raised major part
        :rtype: :class:`VersionInfo`

        ver = semver.VersionInfo.parse("3.4.5")
        ver.bump_major()
        VersionInfo(major=4, minor=0, patch=0, prerelease=None, build=None)
        """
        cls = type(self)
        return cls(self._major + 1)

    def bump_minor(self):
        """
        Raise the minor part of the version, return a new object but leave self
        untouched.

        :return: new object with the raised minor part
        :rtype: :class:`VersionInfo`

        ver = semver.VersionInfo.parse("3.4.5")
        ver.bump_minor()
        VersionInfo(major=3, minor=5, patch=0, prerelease=None, build=None)
        """
        cls = type(self)
        return cls(self._major, self._minor + 1)

    def bump_patch(self):
        """
        Raise the patch part of the version, return a new object but leave self
        untouched.

        :return: new object with the raised patch part
        :rtype: :class:`VersionInfo`

        ver = semver.VersionInfo.parse("3.4.5")
        ver.bump_patch()
        VersionInfo(major=3, minor=4, patch=6, prerelease=None, build=None)
        """
        cls = type(self)
        return cls(self._major, self._minor, self._patch + 1)

    def bump_prerelease(self, token="rc"):
        """
        Raise the prerelease part of the version, return a new object but leave
        self untouched.

        :param token: defaults to 'rc'
        :return: new object with the raised prerelease part
        :rtype: :class:`VersionInfo`

        ver = semver.VersionInfo.parse("3.4.5-rc.1")
        ver.bump_prerelease()
        VersionInfo(major=3, minor=4, patch=5, prerelease='rc.2', \
build=None)
        """
        cls = type(self)
        prerelease = cls._increment_string(self._prerelease or (token or "rc") + ".0")
        return cls(self._major, self._minor, self._patch, prerelease)

    def bump_build(self, token="build"):
        """
        Raise the build part of the version, return a new object but leave self
        untouched.

        :param token: defaults to 'build'
        :return: new object with the raised build part
        :rtype: :class:`VersionInfo`

        ver = semver.VersionInfo.parse("3.4.5-rc.1+build.9")
        ver.bump_build()
        VersionInfo(major=3, minor=4, patch=5, prerelease='rc.1', \
build='build.10')
        """
        cls = type(self)
        build = cls._increment_string(self._build or (token or "build") + ".0")
        return cls(self._major, self._minor, self._patch, self._prerelease, build)

    def compare(self, other):
        """
        Compare self with other.

        :param other: the second version (can be string, a dict, tuple/list, or
             a VersionInfo instance)
        :return: The return value is negative if ver1 < ver2,
             zero if ver1 == ver2 and strictly positive if ver1 > ver2
        :rtype: int

        semver.VersionInfo.parse("1.0.0").compare("2.0.0")
        -1
        semver.VersionInfo.parse("2.0.0").compare("1.0.0")
        1
        semver.VersionInfo.parse("2.0.0").compare("2.0.0")
        0
        semver.VersionInfo.parse("2.0.0").compare(dict(major=2, minor=0, patch=0))
        0
        """
        cls = type(self)
        if isinstance(other, string_types):
            other = cls.parse(other)
        elif isinstance(other, dict):
            other = cls(**other)
        elif isinstance(other, (tuple, list)):
            other = cls(*other)
        elif not isinstance(other, cls):
            raise TypeError(
                "Expected str or {} instance, but got {}".format(
                    cls.__name__, type(other)
                )
            )

        v1 = self.to_tuple()[:3]
        v2 = other.to_tuple()[:3]
        x = cmp(v1, v2)
        if x:
            return x

        rc1, rc2 = self.prerelease, other.prerelease
        rccmp = _nat_cmp(rc1, rc2)

        if not rccmp:
            return 0
        if not rc1:
            return 1
        elif not rc2:
            return -1

        return rccmp

    @comparator
    def __eq__(self, other):
        return self.compare(other) == 0

    @comparator
    def __ne__(self, other):
        return self.compare(other) != 0

    @comparator
    def __lt__(self, other):
        return self.compare(other) < 0

    @comparator
    def __le__(self, other):
        return self.compare(other) <= 0

    @comparator
    def __gt__(self, other):
        return self.compare(other) > 0

    @comparator
    def __ge__(self, other):
        return self.compare(other) >= 0

    def __getitem__(self, index):
        """
        self.__getitem__(index) <==> self[index]

        Implement getitem. If the part requested is undefined, or a part of the
        range requested is undefined, it will throw an index error.
        Negative indices are not supported

        :param Union[int, slice] index: a positive integer indicating the
               offset or a :func:`slice` object
        :raises: IndexError, if index is beyond the range or a part is None
        :return: the requested part of the version at position index

        ver = semver.VersionInfo.parse("3.4.5")
        ver[0], ver[1], ver[2]
        (3, 4, 5)
        """
        if isinstance(index, int):
            index = slice(index, index + 1)

        if (
            isinstance(index, slice)
            and (index.start is not None and index.start < 0)
            or (index.stop is not None and index.stop < 0)
        ):
            raise IndexError("Version index cannot be negative")

        part = tuple(filter(lambda p: p is not None, self.to_tuple()[index]))

        if len(part) == 1:
            part = part[0]
        elif not part:
            raise IndexError("Version part undefined")
        return part

    def __repr__(self):
        s = ", ".join("%s=%r" % (key, val) for key, val in self.to_dict().items())
        return "%s(%s)" % (type(self).__name__, s)

    def __str__(self):
        """str(self)"""
        version = "%d.%d.%d" % (self.major, self.minor, self.patch)
        if self.prerelease:
            version += "-%s" % self.prerelease
        if self.build:
            version += "+%s" % self.build
        return version

    def __hash__(self):
        return hash(self.to_tuple()[:4])

    def finalize_version(self):
        """
        Remove any prerelease and build metadata from the version.

        :return: a new instance with the finalized version string
        :rtype: :class:`VersionInfo`

        str(semver.VersionInfo.parse('1.2.3-rc.5').finalize_version())
        '1.2.3'
        """
        cls = type(self)
        return cls(self.major, self.minor, self.patch)

    def match(self, match_expr):
        """
        Compare self to match a match expression.

        :param str match_expr: operator and version; valid operators are
              <   smaller than
              >   greater than
              >=  greator or equal than
              <=  smaller or equal than
              ==  equal
              !=  not equal
        :return: True if the expression matches the version, otherwise False
        :rtype: bool

        semver.VersionInfo.parse("2.0.0").match(">=1.0.0")
        True
        semver.VersionInfo.parse("1.0.0").match(">1.0.0")
        False
        """
        prefix = match_expr[:2]
        if prefix in (">=", "<=", "==", "!="):
            match_version = match_expr[2:]
        elif prefix and prefix[0] in (">", "<"):
            prefix = prefix[0]
            match_version = match_expr[1:]
        else:
            raise ValueError(
                "match_expr parameter should be in format <op><ver>, "
                "where <op> is one of "
                "['<', '>', '==', '<=', '>=', '!=']. "
                "You provided: %r" % match_expr
            )

        possibilities_dict = {
            ">": (1,),
            "<": (-1,),
            "==": (0,),
            "!=": (-1, 1),
            ">=": (0, 1),
            "<=": (-1, 0),
        }

        possibilities = possibilities_dict[prefix]
        # noinspection PyTypeChecker
        cmp_res = self.compare(match_version)

        return cmp_res in possibilities

    @classmethod
    def parse(cls, version):
        """
        Parse version string to a VersionInfo instance.

        :param version: version string
        :return: a :class:`VersionInfo` instance
        :raises: :class:`ValueError`
        :rtype: :class:`VersionInfo`

        .. versionchanged:: 2.11.0
           Changed method from static to classmethod to
           allow subclasses.

        semver.VersionInfo.parse('3.4.5-pre.2+build.4')
        VersionInfo(major=3, minor=4, patch=5, \
prerelease='pre.2', build='build.4')
        """
        # if "version" is not valid SemVer string with lax conditions used information may be lost
        match = cls._REGEX.match(fix_ver(version))
        version_parts = match.groupdict()

        version_parts["major"] = int(version_parts["major"])
        version_parts["minor"] = int(version_parts["minor"])
        version_parts["patch"] = int(version_parts["patch"])

        return cls(**version_parts)

    def replace(self, **parts):
        """
        Replace one or more parts of a version and return a new
        :class:`VersionInfo` object, but leave self untouched

        .. versionadded:: 2.9.0
           Added :func:`VersionInfo.replace`

        :param dict parts: the parts to be updated. Valid keys are:
          ``major``, ``minor``, ``patch``, ``prerelease``, or ``build``
        :return: the new :class:`VersionInfo` object with the changed
          parts
        :raises: :class:`TypeError`, if ``parts`` contains invalid keys
        """
        version = self.to_dict()
        version.update(parts)
        try:
            return VersionInfo(**version)
        except TypeError:
            unknownkeys = set(parts) - set(self.to_dict())
            error = "replace() got %d unexpected keyword " "argument(s): %s" % (
                len(unknownkeys),
                ", ".join(unknownkeys),
            )
            raise TypeError(error)

    @classmethod
    def isvalid(cls, version):
        """
        Check if the string is a valid semver version.

        .. versionadded:: 2.9.1

        :param str version: the version string to check
        :return: True if the version string is a valid semver version, False
                 otherwise.
        :rtype: bool
        """
        try:
            # noinspection PyTypeChecker
            cls.parse(version)
            return True
        except ValueError:
            return False


def compare(ver1, ver2):
    """
    Compare two versions strings.

    :param ver1: version string 1
    :param ver2: version string 2
    :return: The return value is negative if ver1 < ver2,
             zero if ver1 == ver2 and strictly positive if ver1 > ver2
    :rtype: int

    semver.compare("1.0.0", "2.0.0")
    -1
    semver.compare("2.0.0", "1.0.0")
    1
    semver.compare("2.0.0", "2.0.0")
    0
    """
    v1 = VersionInfo.parse(ver1)
    return v1.compare(ver2)
