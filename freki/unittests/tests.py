# =============================================================================
# Serialization Testcases
# =============================================================================
import os
from collections import namedtuple
from io import StringIO
from unittest import TestCase
from freki.serialize import *
import run_freki


class ConstructorTests(TestCase):
    def test_doc(self):
        fd = FrekiDoc()
        self.assertIsNotNone(fd)

    def test_line(self):
        l = FrekiLine()
        self.assertIsNotNone(l)

    def test_block(self):
        b = FrekiBlock()
        self.assertIsNotNone(b)

class ReadTest(TestCase):
    def setUp(self):
        self.fd_path = os.path.join(os.path.dirname(__file__), '16.txt')

    def test_read(self):
        fd = FrekiDoc.read(self.fd_path)
        self.assertEqual(len(list(fd.lines())), 698)
        self.assertEqual(len(list(fd.blocks)), 458)

    def test_write(self):
        fd = FrekiDoc.read(self.fd_path)
        str(fd)


# =============================================================================
# Freki Tests
# =============================================================================
class TetMLTest(TestCase):
    def setUp(self):
        self.tetml_path = os.path.join(os.path.dirname(__file__), '1076941.tetml')
        self.freki_path = os.path.join(os.path.dirname(__file__), '1076941.freki')

    def test_read(self):
        args = namedtuple('args', ('format', 'infile', 'outfile'))
        args.format = 'tetml'
        args.infile = self.tetml_path
        inout = StringIO()
        args.outfile = inout
        args.block = 0.
        args.deindent_blocks = False

        # Run the tetml to freki conversion
        run_freki.run(args)

        # Retrieve the contents of the output
        inout.flush()
        inout.seek(0)
        outstr = inout.read()

        # Compare that against the saved document.
        freki_f = open(self.freki_path, 'r')

        self.assertEqual(freki_f.read(), outstr)