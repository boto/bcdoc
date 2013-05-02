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
from six.moves import html_parser


class HelpParser(html_parser.HTMLParser):
    """
    A simple HTML parser.  Really focused only on
    the subset of HTML that shows up in the documentation strings
    found in the models.
    """

    def __init__(self, doc):
        html_parser.HTMLParser.__init__(self)
        self.doc = doc
        self.unhandled_tags = []

    def handle_starttag(self, tag, attrs):
        handler_name = 'start_%s' % tag
        if hasattr(self.doc.style, handler_name):
            s = getattr(self.doc.style, handler_name)(attrs)
            if s:
                self.doc.get_current_paragraph().write(s)
        else:
            self.unhandled_tags.append(tag)

    def handle_endtag(self, tag):
        handler_name = 'end_%s' % tag
        if hasattr(self.doc.style, handler_name):
            s = getattr(self.doc.style, handler_name)()
            if s:
                self.doc.get_current_paragraph().write(s)
        else:
            self.doc.get_current_paragraph().write(' ')

    def handle_data(self, data):
        data = data.replace('\n', '')
        if not data:
            return
        if data.isspace():
            data = ' '
        words = data.split()
        words = self.doc.translate_words(words)
        data = ' '.join(words)
        begin_space = data[0].isspace()
        end_space = data[-1].isspace()
        if begin_space:
            if len(data) > 0 and not data[0].isupper():
                data = ' ' + data
        if end_space:
            if len(data) > 0 and data[-1] != '.':
                data = data + ' '
        self.doc.handle_data(data)

    def handle_data(self, data):
        if data.isspace():
            data = ' '
        else:
            end_space = data[-1].isspace()
            words = data.split()
            words = self.doc.translate_words(words)
            data = ' '.join(words)
            if end_space:
                data += ' '
        self.doc.handle_data(data)
