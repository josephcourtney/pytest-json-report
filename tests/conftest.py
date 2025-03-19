import importlib.util
import json

import pytest

has_xdist = importlib.util.find_spec("xdist") is not None

pytest_plugins = "pytester"
miss_map = {
    "V": "Different values",
    "K": "Different keys",
    "T": "Different types",
}
FILE = """
from __future__ import print_function
import sys
import pytest


@pytest.fixture
def setup_teardown_fixture(request):
    print('setup')
    print('setuperr', file=sys.stderr)
    def fn():
        print('teardown')
        print('teardownerr', file=sys.stderr)
    request.addfinalizer(fn)

@pytest.fixture
def fail_setup_fixture(request):
    assert False

@pytest.fixture
def fail_teardown_fixture(request):
    def fn():
        assert False
    request.addfinalizer(fn)


def test_pass():
    assert True

def test_fail_with_fixture(setup_teardown_fixture):
    print('call')
    print('callerr', file=sys.stderr)
    assert False

@pytest.mark.xfail(reason='testing xfail')
def test_xfail():
    assert False

@pytest.mark.xfail(reason='testing xfail')
def test_xfail_but_passing():
    assert True

def test_fail_during_setup(fail_setup_fixture):
    assert True

def test_fail_during_teardown(fail_teardown_fixture):
    assert True

@pytest.mark.skipif(True, reason='testing skip')
def test_skip():
    assert False

def test_fail_nested():
    def baz(o=1):
        c = 3
        return 2 - c - None
    def bar(m, n=5):
        b = 2
        print(m)
        print('bar')
        return baz()
    def foo():
        a = 1
        print('foo')
        v = [bar(x) for x in range(3)]
        return v
    foo()

@pytest.mark.parametrize('x', [1, 2])
def test_parametrized(x):
    assert x == 1
"""


@pytest.fixture
def misc_testdir(testdir):
    testdir.makepyfile(FILE)
    return testdir


@pytest.fixture
def json_data(make_json):
    return make_json()


@pytest.fixture
def tests(json_data):
    return tests_only(json_data)


def tests_only(json_data):
    return {test["nodeid"].split("::")[-1][5:]: test for test in json_data["tests"]}


@pytest.fixture(params=[0, 1, 4])
def num_processes(request):
    return request.param


@pytest.fixture
def make_json(num_processes, testdir):
    def func(content=FILE, args=None, path=".report.json"):
        if args is None:
            base_args = ["-vv", "-p", "pytest_json_report.plugin", "--json-report"]
            if has_xdist and num_processes > 1:
                base_args.append(f"-n={num_processes}")
            args = base_args
        testdir.makepyfile(content)
        result = testdir.runpytest(*args)
        report_path = testdir.tmpdir / path
        if not report_path.exists():
            pytest.fail(f"Report file {path} was not generated. Run result: {result.stdout.str()}")
        with open(str(report_path), encoding="utf-8") as f:
            return json.load(f)

    return func


def diff(a, b, path=None):
    if path is None:
        path = []
    if path and path[-1] != "longrepr":
        return
    if type(a) != type(b):
        yield ("T", path, a, b)
        return
    if type(a) == dict:
        a_keys = sorted(a.keys())
        b_keys = sorted(b.keys())
        if a_keys != b_keys:
            yield ("K", path, a_keys, b_keys)
            return
        for ak, bk in zip(a_keys, b_keys, strict=False):
            for item in diff(a[ak], b[bk], [*path, str(ak)]):
                yield item
        return
    if type(a) == list:
        for i, (ai, bi) in enumerate(zip(a, b, strict=False)):
            for item in diff(ai, bi, [*path, str(i)]):
                yield item
        return
    if a != b:
        yield ("V", path, repr(a), repr(b))
    return


@pytest.fixture
def match_reports():
    # Implement the match_reports fixture here
    pass
