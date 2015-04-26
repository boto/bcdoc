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
import mock

from bcdoc.restdoc import ReSTDocument, DocumentStructure


class TestReSTDocument(unittest.TestCase):

    def test_write(self):
        doc = ReSTDocument()
        doc.write('foo')
        self.assertEqual(doc.getvalue(), six.b('foo'))

    def test_writeln(self):
        doc = ReSTDocument()
        doc.writeln('foo')
        self.assertEqual(doc.getvalue(), six.b('foo\n'))

    def test_include_doc_string(self):
        doc = ReSTDocument()
        doc.include_doc_string('<p>this is a <code>test</code></p>')
        self.assertEqual(doc.getvalue(), six.b('\n\nthis is a ``test`` \n\n'))
        
    def test_remove_doc_string(self):
        doc = ReSTDocument()
        doc.writeln('foo')
        doc.include_doc_string('<p>this is a <code>test</code></p>')
        doc.remove_last_doc_string()
        self.assertEqual(doc.getvalue(), six.b('foo\n'))


class TestDocumentStructure(unittest.TestCase):
    def setUp(self):
        self.name = 'mydoc'
        self.event_emitter = mock.Mock()
        self.doc_structure = DocumentStructure(
            self.name, self.event_emitter)

    def test_name(self):
        self.assertEqual(self.doc_structure.name, self.name)

    def test_path(self):
        self.assertEqual(self.doc_structure.path, [self.name])
        self.doc_structure.path = ['foo']
        self.assertEqual(self.doc_structure.path, ['foo'])

    def test_add_new_section(self):
        section = self.doc_structure.add_new_section('mysection')

        # Ensure the name of the section is correct
        self.assertEqual(section.name, 'mysection')

        # Ensure we can get the section.
        self.assertEqual(
            self.doc_structure.get_section('mysection'), section)

        # Ensure the path is correct
        self.assertEqual(section.path, ['mydoc', 'mysection'])

        # Ensure some of the necessary attributes are passed to the
        # the section.
        self.assertEqual(section.style.indentation,
                         self.doc_structure.style.indentation)
        self.assertEqual(section.translation_map,
                         self.doc_structure.translation_map)
        self.assertEqual(section.hrefs,
                         self.doc_structure.hrefs)

        # Ensure the event fired is as expected
        events_called = self.event_emitter.emit.call_args_list
        self.assertEqual(len(events_called), 1)
        self.assertEqual(
            events_called[0],
            mock.call('docs-adding-section.mydoc-mysection', section=section))

    def test_delete_section(self):
        section = self.doc_structure.add_new_section('mysection')
        self.assertEqual(
            self.doc_structure.get_section('mysection'), section)
        self.doc_structure.delete_section('mysection')
        with self.assertRaises(KeyError):
            section.get_section('mysection')

    def test_create_sections_at_instantiation(self):
        sections = ['intro', 'middle', 'end']
        self.doc_structure = DocumentStructure(
            self.name, self.event_emitter, section_names=sections)
        events_called = self.event_emitter.emit.call_args_list

        # Ensure the sections are created, exist, and are emitted.
        self.assertEqual(len(events_called), 3)
        for i, section in enumerate(sections):
            self.assertEqual(
                events_called[i],
                mock.call('docs-adding-section.mydoc-%s' % section,
                          section=self.doc_structure.get_section(section)))

    def test_flush_structure(self):
        section = self.doc_structure.add_new_section('mysection')
        subsection = section.add_new_section('mysubsection')
        self.doc_structure.writeln('1')
        section.writeln('2')
        subsection.writeln('3')
        second_section = self.doc_structure.add_new_section('mysection2')
        second_section.writeln('4')
        contents = self.doc_structure.flush_structure()

        # Ensure the contents were flushed out correctly
        self.assertEqual(contents, six.b('1\n2\n3\n4\n'))

        # Ensure the sections are emitted.
        events_called = self.event_emitter.emit.call_args_list
        self.assertEqual(len(events_called), 7)
        events_called = events_called[3:]
        self.assertEqual(
            events_called[0],
            mock.call('docs-flushing-structure.mydoc',
                      structure=self.doc_structure))
        self.assertEqual(
            events_called[1],
            mock.call('docs-flushing-structure.mydoc-mysection',
                      structure=section))
        self.assertEqual(
            events_called[2],
            mock.call('docs-flushing-structure.mydoc-mysection-mysubsection',
                      structure=subsection))
        self.assertEqual(
            events_called[3],
            mock.call('docs-flushing-structure.mydoc-mysection2',
                      structure=second_section))

    def test_flush_structure_hrefs(self):
        section = self.doc_structure.add_new_section('mysection')
        section.writeln('section contents')
        self.doc_structure.hrefs['foo'] = 'www.foo.com'
        section.hrefs['bar'] = 'www.bar.com'
        contents = self.doc_structure.flush_structure()
        self.assertEqual(
            contents,
            six.b('\n\n.. _foo: www.foo.com\n.. _bar: www.bar.com\n'
                  'section contents\n')
        )
