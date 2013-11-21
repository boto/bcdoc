# Copyright (c) 2012-2013 Mitch Garnaat http://garnaat.org/
# Copyright 2012-2013 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish, dis-
# tribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the fol-
# lowing conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
# OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABIL-
# ITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT
# SHALL THE AUTHOR BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#
import unittest

import six

from bcdoc.style import ReSTStyle
from bcdoc.restdoc import ReSTDocument


class TestStyle(unittest.TestCase):

    def test_spaces(self):
        style = ReSTStyle(None, 4)
        self.assertEqual(style.spaces(), '')
        style.indent()
        self.assertEqual(style.spaces(), '    ')
        style.indent()
        self.assertEqual(style.spaces(), '        ')
        style.dedent()
        self.assertEqual(style.spaces(), '    ')
        style.dedent()
        self.assertEqual(style.spaces(), '')
        style.dedent()
        self.assertEqual(style.spaces(), '')

    def test_bold(self):
        style = ReSTStyle(ReSTDocument())
        style.bold('foobar')
        self.assertEqual(style.doc.getvalue(), six.b('**foobar** '))

    def test_italics(self):
        style = ReSTStyle(ReSTDocument())
        style.italics('foobar')
        self.assertEqual(style.doc.getvalue(), six.b('*foobar* '))

    def test_code(self):
        style = ReSTStyle(ReSTDocument())
        style.code('foobar')
        self.assertEqual(style.doc.getvalue(), six.b('``foobar`` '))

    def test_h1(self):
        style = ReSTStyle(ReSTDocument())
        style.h1('foobar fiebaz')
        self.assertEqual(style.doc.getvalue(),
                         six.b('\n\n*************\nfoobar fiebaz\n*************\n\n'))
        
    def test_h2(self):
        style = ReSTStyle(ReSTDocument())
        style.h2('foobar fiebaz')
        self.assertEqual(style.doc.getvalue(),
                         six.b('\n\n=============\nfoobar fiebaz\n=============\n\n'))
        
    def test_h3(self):
        style = ReSTStyle(ReSTDocument())
        style.h3('foobar fiebaz')
        self.assertEqual(style.doc.getvalue(),
                         six.b('\n\n-------------\nfoobar fiebaz\n-------------\n\n'))
        
    def test_ref(self):
        style = ReSTStyle(ReSTDocument())
        style.ref('foobar', 'http://foo.bar.com')
        self.assertEqual(style.doc.getvalue(),
                         six.b(':doc:`foobar <http://foo.bar.com>`'))

    def test_examples(self):
        style = ReSTStyle(ReSTDocument())
        self.assertTrue(style.doc.keep_data)
        style.start_examples()
        self.assertFalse(style.doc.keep_data)
        style.end_examples()
        self.assertTrue(style.doc.keep_data)
        
    def test_codeblock(self):
        style = ReSTStyle(ReSTDocument())
        style.codeblock('foobar')
        self.assertEqual(style.doc.getvalue(),
                         six.b('::\n\n  foobar\n\n\n'))

    def test_toctree_html(self):
        style = ReSTStyle(ReSTDocument())
        style.doc.target = 'html'
        style.toctree()
        style.tocitem('foo')
        style.tocitem('bar')
        self.assertEqual(style.doc.getvalue(),
                         six.b('\n.. toctree::\n  :maxdepth: 1\n  :titlesonly:\n\n  foo\n  bar\n'))
        
    def test_toctree_man(self):
        style = ReSTStyle(ReSTDocument())
        style.doc.target = 'man'
        style.toctree()
        style.tocitem('foo')
        style.tocitem('bar')
        self.assertEqual(style.doc.getvalue(),
                         six.b('\n\n\n* foo\n\n\n* bar\n\n'))
        
