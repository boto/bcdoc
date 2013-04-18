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

from six.moves import cStringIO
import textwrap


class Paragraph(object):

    def __init__(self, doc, width, initial_indent):
        self.doc = doc
        self.width = width
        self.initial_indent = initial_indent
        self.subsequent_indent = initial_indent
        self.lines_before = 0
        self.lines_after = 1
        self.fp = cStringIO()
        self.current_char = None

    def write(self, s):
        if self.doc.keep_data:
            self.fp.write(s)
            if s:
                self.current_char = s[-1]

    def wrap(self):
        init_indent = self.doc.style.spaces(self.initial_indent)
        sub_indent = self.doc.style.spaces(self.subsequent_indent)
        s = textwrap.fill(self.fp.getvalue(), self.width,
                          initial_indent=init_indent,
                          subsequent_indent=sub_indent,
                          break_on_hyphens=False)
        return '\n' * self.lines_before + s + '\n' * self.lines_after
