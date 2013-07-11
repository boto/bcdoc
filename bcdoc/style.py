# Copyright 2012-2013 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.


class BaseStyle(object):

    def __init__(self, doc, indent_width=2):
        self.doc = doc
        self.indent_width = indent_width
        self._indent = 0
        self.keep_data = True

    def new_paragraph(self):
        return '\n%s' % self.spaces()

    def indent(self):
        self._indent += 1

    def dedent(self):
        if self._indent > 0:
            self._indent -= 1

    def spaces(self):
        return ' ' * (self._indent * self.indent_width)

    def bold(self, s):
        return s

    def ref(self, link, title=None):
        return link

    def h2(self, s):
        return s

    def h3(self, s):
        return s

    def underline(self, s):
        return s

    def italics(self, s):
        return s


class ReSTStyle(BaseStyle):

    def __init__(self, doc, indent_width=2):
        BaseStyle.__init__(self, doc, indent_width)
        self.do_p = True
        self.a_href = None

    def new_paragraph(self):
        if self.do_p:
            self.doc.write('\n\n%s' % self.spaces())

    def new_line(self):
        if self.do_p:
            self.doc.write('\n%s' % self.spaces())

    def start_bold(self, attrs=None):
        self.doc.write('**')

    def end_bold(self):
        self.doc.write('** ')

    def start_b(self, attrs=None):
        self.doc.do_translation = True
        self.start_bold(attrs)

    def end_b(self):
        self.doc.do_translation = False
        self.doc.write('** ')

    def bold(self, s):
        if s:
            self.start_bold()
            self.doc.write(s)
            self.end_bold()

    def ref(self, title, link=None):
        if link is None:
            link = title
        self.doc.write(':doc:`%s <%s>`' % (title, link))

    def _heading(self, s, border_char):
        border = border_char * len(s)
        self.new_paragraph()
        self.doc.write('%s\n%s\n%s' % (border, s, border))
        self.new_paragraph()

    def h1(self, s):
        self._heading(s, '*')

    def h2(self, s):
        self._heading(s, '=')

    def h3(self, s):
        self._heading(s, '-')

    def start_italics(self, attrs=None):
        self.doc.write('*')

    def end_italics(self):
        self.doc.write('* ')

    def italics(self, s):
        if s:
            self.start_italics()
            self.doc.write(s)
            self.end_italics()

    def start_p(self, attrs=None):
        if self.do_p:
            self.doc.write('\n\n%s' % self.spaces())

    def end_p(self):
        if self.do_p:
            self.doc.write('\n\n')

    def start_code(self, attrs=None):
        self.doc.do_translation = True
        self.doc.write('``')

    def end_code(self):
        self.doc.do_translation = False
        self.doc.write('`` ')

    def code(self, s):
        if s:
            self.start_code()
            self.doc.write(s)
            self.end_code()

    def start_note(self, attrs=None):
        self.new_paragraph()
        self.doc.write('.. note::')
        self.indent()
        self.new_paragraph()

    def end_note(self):
        self.dedent()
        self.new_paragraph()

    def start_important(self, attrs=None):
        self.new_paragraph()
        self.doc.write('.. warning::')
        self.indent()
        self.new_paragraph()

    def end_important(self):
        self.dedent()
        self.new_paragraph()

    def start_a(self, attrs=None):
        if attrs:
            for attr_key, attr_value in attrs:
                if attr_key == 'href':
                    self.a_href = attr_value
                    self.doc.write('`')
        else:
            self.doc.write(' ')
        self.doc.do_translation = True

    def end_a(self):
        self.doc.do_translation = False
        if self.a_href:
            self.doc.write(' <%s>' % self.a_href)
            self.a_href = None
            self.doc.write('`_')
        self.doc.write(' ')

    def start_i(self, attrs=None):
        self.doc.do_translation = True
        self.start_italics()

    def end_i(self):
        self.doc.do_translation = False
        self.end_italics()

    def start_li(self, attrs=None):
        self.do_p = False
        self.doc.write('* ')

    def end_li(self):
        self.do_p = True
        self.new_line()

    def li(self, s):
        if s:
            self.start_li()
            self.doc.writeln(s)
            self.end_li()

    def start_ul(self, attrs=None):
        self.new_paragraph()

    def end_ul(self):
        self.new_paragraph()

    def start_ol(self, attrs=None):
        # TODO: Need to control the bullets used for LI items
        self.new_paragraph()

    def end_ol(self):
        self.new_paragraph()

    def start_examples(self, attrs=None):
        self.doc.keep_data = False

    def end_examples(self):
        self.doc.keep_data = True

    def start_fullname(self, attrs=None):
        self.doc.keep_data = False

    def end_fullname(self):
        self.doc.keep_data = True

    def start_codeblock(self, attrs=None):
        self.doc.write('::')
        self.indent()
        self.new_paragraph()

    def end_codeblock(self):
        self.dedent()
        self.new_paragraph()

    def codeblock(self, code):
        """
        Literal code blocks are introduced by ending a paragraph with
        the special marker ::.  The literal block must be indented
        (and, like all paragraphs, separated from the surrounding
        ones by blank lines).
        """
        self.start_codeblock()
        self.doc.writeln(code)
        self.end_codeblock()

    def toctree(self):
        if self.doc.target == 'html':
            self.doc.write('\n.. toctree::\n')
            self.doc.write('  :maxdepth: 1\n')
            self.doc.write('  :titlesonly:\n\n')
        else:
            self.start_ul()

    def tocitem(self, item, file_name=None):
        if self.doc.target == 'man':
            self.li(item)
        else:
            if file_name:
                self.doc.writeln('  %s' % file_name)
            else:
                self.doc.writeln('  %s' % item)

