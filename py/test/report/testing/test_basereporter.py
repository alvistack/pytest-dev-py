import py
from py.__.test.report.base import BaseReporter
from py.__.test.event import EventBus
from py.__.test import event
from py.__.test.runner import OutcomeRepr
from py.__.test.report.base import getrelpath, getmodpath, repr_pythonversion
from py.__.test.testing import setupdata
import sys

class TestBaseReporter:
    def test_activate(self):
        bus = EventBus()
        rep = BaseReporter(bus=bus)
        assert bus._subscribers
        assert rep.processevent in bus._subscribers
        rep.deactivate()
        assert not bus._subscribers

    def test_dispatch_to_matching_method(self):
        l = []
        class MyReporter(BaseReporter):
            def rep_TestrunStart(self, ev):
                l.append(ev)
        rep = MyReporter()
        ev = event.TestrunStart()
        rep.processevent(ev)
        assert len(l) == 1
        assert l[0] is ev

    def test_dispatch_to_default(self):
        l = []
        class MyReporter(BaseReporter):
            def rep(self, ev):
                l.append(ev)
        rep = MyReporter()
        ev = event.NOP()
        rep.processevent(ev)
        assert len(l) == 1
        assert l[0] is ev

    def test_TestItemReport_one(self):
        for outcome in 'passed skipped failed'.split():
            rep = BaseReporter()
            ev = event.ItemTestReport(None, **{outcome:True})
            rep.processevent(ev)
            assert getattr(rep, '_' + outcome) == [ev]

    def test_CollectionReport(self):
        for outcome in 'skipped failed'.split():
            rep = BaseReporter()
            ev = event.CollectionReport(None, None, **{outcome:True})
            rep.processevent(ev)
            assert getattr(rep, '_' + outcome) == [ev]

    def test_skip_reasons(self):
        rep = BaseReporter()
        class longrepr:
            path = 'xyz'
            lineno = 3
            message = "justso"
        out1 = OutcomeRepr(None, None, longrepr)
        out2 = OutcomeRepr(None, None, longrepr)
        ev1 = event.CollectionReport(None, None, skipped=out1)
        ev2 = event.ItemTestReport(None, skipped=out2)
        rep.processevent(ev1)
        rep.processevent(ev2)
        assert len(rep._skipped) == 2
        l = rep._folded_skips()
        assert len(l) == 1
        num, fspath, lineno, reason = l[0]
        assert num == 2
        assert fspath == longrepr.path
        assert lineno == longrepr.lineno
        assert reason == longrepr.message

def test_getmodpath_cases():
    tmpdir = py.test.ensuretemp("test_getmodpath_cases") 
    pkgdir = tmpdir.join("test_getmodpath") 
    pkgdir.ensure("__init__.py") 
    nopkgdir = tmpdir.ensure("nopkg", dir=1) 
    def checkpkg(names, expected):
        fcol = setupdata.getexamplecollector(names, tmpdir=pkgdir)
        assert getmodpath(fcol) == pkgdir.basename + "." + expected 
    def checknopkg(names, expected):
        fcol = setupdata.getexamplecollector(names, tmpdir=nopkgdir)
        assert getmodpath(fcol) == expected 

    for names in (
        'mod.py test_f1           mod.test_f1', 
        'mod.py TestA () test_m1  mod.TestA().test_m1', 
        'mod.py test_g1           mod.test_g1', 
        'mod.py test_g1 [0]       mod.test_g1[0]', 
    ):
        names = names.split()
        expected = names.pop()
        yield checkpkg, names, expected 
        yield checknopkg, names, expected 

def test_repr_python_version():
    py.magic.patch(sys, 'version_info', (2, 5, 1, 'final', 0))
    try:
        assert repr_pythonversion() == "2.5.1-final-0"
        py.std.sys.version_info = x = (2,3)
        assert repr_pythonversion() == str(x) 
    finally: 
        py.magic.revert(sys, 'version_info') 

def test_getrelpath():
    curdir = py.path.local()
    sep = curdir.sep
    s = getrelpath(curdir, curdir.join("hello", "world"))
    assert s == "hello" + sep + "world"

    s = getrelpath(curdir, curdir.dirpath().join("sister"))
    assert s == ".." + sep + "sister"
    assert getrelpath(curdir, curdir.dirpath()) == ".."
    
    assert getrelpath(curdir, "hello") == "hello"