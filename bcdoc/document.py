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

from .paragraph import Paragraph
from .style import ReSTStyle
from .htmlparser import HelpParser


class Document(object):

    def __init__(self, session):
        self.session = session
        self.style = ReSTStyle(self)
        self.width = 80
        self.help_parser = HelpParser(self)
        self.paragraphs = []
        self.keep_data = True
        self.do_translation = False
        self.translation_map = {}
        self.build_translation_map()
        self.initial_indent = 0
        self.subsequent_indent = 0

    def build_translation_map(self):
        pass

    def indent(self):
        self.initial_indent += 1

    def dedent(self):
        self.initial_indent -= 1

    def translate_words(self, words):
        return [self.translation_map.get(w, w) for w in words]

    def add_paragraph(self):
        self.paragraphs.append(Paragraph(self, self.width,
                                         self.initial_indent))
        return self.paragraphs[-1]

    def get_current_paragraph(self):
        if len(self.paragraphs) == 0:
            self.add_paragraph(self)
        return self.paragraphs[-1]

    def do_title(self, title):
        self.add_paragraph().write(self.style.h1(title))
        self.add_paragraph()

    def do_description(self, description):
        self.add_paragraph().write(self.style.h2('DESCRIPTION'))
        if description:
            self.add_paragraph()
            self.help_parser.feed(description)

    def handle_data(self, data):
        if data and self.keep_data:
            paragraph = self.get_current_paragraph()
            if paragraph.current_char is None and data.isspace():
                pass
            else:
                paragraph.write(data)

    def render(self, fp):
        for paragraph in self.paragraphs:
            fp.write(paragraph.wrap())

    def build(self, object):
        pass
