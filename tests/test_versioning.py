"""Tests output obtained by parsing version info across languages"""
import pytest
from packaging.specifiers import SpecifierSet

from dependencies.helper import fix_constraint, resolve_version


@pytest.mark.parametrize(
    ("language", "ver_constraint", "expected_output"),
    [
        # Caret requirements
        ("python", "^1.2.3", ">=1.2.3,<2.0.0"),
        ("python", "^1.2", ">=1.2.0,<2.0.0"),
        ("python", "^1", ">=1.0.0,<2.0.0"),
        ("python", "^0.2.3", ">=0.2.3,<0.3.0"),
        ("python", "^0.0.3", ">=0.0.3,<0.0.4"),
        ("python", "^0.0", ">=0.0.0,<0.1.0"),
        ("python", "^0", ">=0.0.0,<1.0.0"),
        # Tilde requirements
        ("python", "~1.2.3", ">=1.2.3,<1.3.0"),
        ("python", "~1.2", ">=1.2.0,<1.3.0"),
        ("python", "~1", ">=1.0.0,<2.0.0"),
        ("python", "~0.3.2", ">=0.3.2,<0.4.0"),
        ("python", "~0.0.5", ">=0.0.5,<0.1.0"),
        # exact same logic for JavaScript
        ("javascript", "^1.2.3", ">=1.2.3,<2.0.0"),
        ("javascript", "^1.2", ">=1.2.0,<2.0.0"),
        ("javascript", "^1", ">=1.0.0,<2.0.0"),
        ("javascript", "^0.2.3", ">=0.2.3,<0.3.0"),
        ("javascript", "^0.0.3", ">=0.0.3,<0.0.4"),
        ("javascript", "^0.0", ">=0.0.0,<0.1.0"),
        ("javascript", "^0", ">=0.0.0,<1.0.0"),
        ("javascript", "~1.2.3", ">=1.2.3,<1.3.0"),
        ("javascript", "~0.3.2", ">=0.3.2,<0.4.0"),
        # exact requirements
        ("javascript", "1.2.3", "==1.2.3"),
        # wildcard requirements
        ("javascript", "1.2.x", "==1.2.*"),
        ("javascript", "*", ""),
        ("javascript", "", ""),
        ("javascript", "1.2.3 - 1.2.5", ">=1.2.3,<=1.2.5"),
        # Go Minimum version specification
        ("go", "v1.2.3", ">=v1.2.3"),
        # C# set bassed notation
        ("cs", "1.0", ">=1.0"),
        ("cs", "(1.0,)", ">1.0"),
        ("cs", "[1.0]", "==1.0"),
        ("cs", "(,1.0]", "<=1.0"),
        ("cs", "(,1.0)", "<1.0"),
        ("cs", "[1.0,2.0]", ">=1.0,<=2.0"),
        ("cs", "(1.0,2.0)", ">1.0,<2.0"),
        ("cs", "[1.0,2.0)", ">=1.0,<2.0"),
        ("php", "^1.2.3", ">=1.2.3,<2.0.0"),
        ("php", "^0.3", ">=0.3.0,<0.4.0"),
        ("php", "^0.0.3", ">=0.0.3,<0.0.4"),
        ("php", "1.0.0 - 2.1.0", ">=1.0.0,<=2.1.0"),
        ("php", "~1.2", ">=1.2,<2.0.0"),
        ("php", "~1.2.3", ">=1.2.3,<1.3.0"),
        ("rust", "1.2.3", ">=1.2.3,<2.0.0"),
        ("rust", "1.2", ">=1.2.0,<2.0.0"),
        ("rust", "1", ">=1.0.0,<2.0.0"),
        ("rust", "0.2.3", ">=0.2.3,<0.3.0"),
        ("rust", "0.2", ">=0.2.0,<0.3.0"),
        ("rust", "0.0.3", ">=0.0.3,<0.0.4"),
        ("rust", "0.0", ">=0.0.0,<0.1.0"),
        ("rust", "0", ">=0.0.0,<1.0.0"),
        # alt syntax for carets
        ("rust", "^0.2.3", ">=0.2.3,<0.3.0"),
        ("rust", "~1.2.3", ">=1.2.3,<1.3.0"),
        ("rust", "~1.2", ">=1.2.0,<1.3.0"),
        ("rust", "~1", ">=1.0.0,<2.0.0"),
        # ~ in Python[poetry], JavaScript
        # Ignores git and URL dependencies
        # Ignores directives other than require in Go
        # Ignores stability constraints in PHP
    ],
)
def test_simple_dependency_parsing(language, ver_constraint, expected_output):
    """Test direct single entry logical conversion of requirement constraints"""
    resolved_constraints = fix_constraint(language, ver_constraint)
    assert resolved_constraints == [SpecifierSet(expected_output)]


@pytest.mark.parametrize(
    ("language", "ver_constraint", "req_constraint"),
    [
        # logical ORs
        ("javascript", "<1.2.3 || <1.2.2", "<1.2.3"),
        ("php", "1.0.*", ">=1.0,<1.1"),
        ("php", ">=1.0 <1.1 || <=1.0", "1.0.*"),
        ("rust", "*", ">=0.0.0"),
        ("rust", "1.*", ">=1.0.0,<2.0.0"),
        ("rust", "1.2.*", ">=1.2.0,<1.3.0"),
    ],
)
def test_equivalent_dependency_parsing(language, ver_constraint, req_constraint):
    """Tests equivalent version resolutions when latest compatible ver is to be considered"""
    vers = [".".join(list(str(ver).rjust(3, "0"))) for ver in range(0, 1000)]
    assert resolve_version(
        vers, fix_constraint(language, ver_constraint)
    ) == resolve_version(vers, fix_constraint(language, req_constraint))
