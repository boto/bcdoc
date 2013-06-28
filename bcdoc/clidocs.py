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
import logging
from six.moves import cStringIO
from botocore.hooks import HierarchicalEmitter
from bcdoc.docstringparser import DocStringParser
from bcdoc.style import ReSTStyle

LOG = logging.getLogger(__name__)


class ReSTDocument(object):

    def __init__(self, fp=None, target='man'):
        if fp is None:
            fp = cStringIO()
        self.fp = fp
        self.style = ReSTStyle(self)
        self.target = target
        self.parser = DocStringParser(self)
        self.keep_data = True
        self.do_translation = False
        self.translation_map = {}
        #self.build_translation_map()

    def write(self, s):
        # self.fp.write('%s%s' % (self.style.spaces(), s))
        self.fp.write(s)

    def build_translation_map(self):
        pass

    def translate_words(self, words):
        return [self.translation_map.get(w, w) for w in words]

    def handle_data(self, data):
        if data and self.keep_data:
            # Some of the JSON service descriptions have
            # Unicode constants embedded in the doc strings
            # which cause UnicodeEncodeErrors in Python 2.x
            try:
                self.write(data)
            except UnicodeEncodeError:
                self.write(data.encode('utf-8'))

    def include_doc_string(self, doc_string):
        if doc_string:
            self.parser.feed(doc_string)


class CLIDocumentEventHandler(object):

    def __init__(self):
        pass

    def initialize(self, session):
        pass


class ProviderDocumentEventHandler(CLIDocumentEventHandler):

    def initialize(self, session):
        CLIDocumentEventHandler.initialize(self, session)
        session.register('doc-title.Provider.*', self.title)
        session.register('doc-description.Provider.*', self.description)
        session.register('doc-synopsis-start.Provider.*', self.synopsis)
        session.register('doc-options-start.Provider.*', self.options)
        session.register('doc-option.Provider.*.*', self.option)
        session.register('doc-subitems-start.Provider.*', self.subitems)
        session.register('doc-subitem.Provider.*.*', self.subitem)

    def title(self, event_name, provider, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h1(provider.name)

    def description(self, event_name, provider, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Description')
        doc.include_doc_string(help_command.description)

    def synopsis(self, event_name, provider, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Synopsis')
        doc.style.codeblock(help_command.synopsis)
        doc.include_doc_string(help_command.help_usage)
        doc.style.new_paragraph()

    def options(self, event_name, provider, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Options')

    def option(self, event_name, argument, help_command, **kwargs):
        doc = help_command.doc
        doc.write('``%s`` (%s)\n' % (argument.cli_name,
                                      argument.cli_type_name))
        doc.style.indent()
        doc.include_doc_string(argument.documentation)
        doc.style.dedent()
        doc.style.new_paragraph()
        if argument.choices:
            doc.style.start_ul()
            for choice in argument.choices:
                doc.style.li(choice)
            doc.style.end_ul()

    def subitems(self, event_name, provider, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Available Services')
        doc.style.toctree()

    def subitem(self, event_name, provider, service_name,
                help_command, **kwargs):
        doc = help_command.doc
        if doc.target == 'man':
            doc.write('* %s\n' % service_name)
        else:
            doc.write('  %s/index\n' % service_name)


class ServiceDocumentEventHandler(CLIDocumentEventHandler):

    def initialize(self, session):
        CLIDocumentEventHandler.initialize(self, session)
        session.register('doc-title.Service.*', self.title)
        session.register('doc-description.Service.*', self.description)
        session.register('doc-subitems-start.Service.*', self.subitems)
        session.register('doc-subitem.Service.*.*', self.subitem)

    def build_translation_map(self):
        for op in self.service.operations:
            self.translation_map[op.name] = op.cli_name

    def title(self, event_name, service, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h1(service.endpoint_prefix)

    def description(self, event_name, service, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Description')
        doc.include_doc_string(service.documentation)

    def subitems(self, event_name, service, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Available Commands')
        doc.style.toctree()

    def subitem(self, event_name, service, operation_name,
                help_command, **kwargs):
        doc = help_command.doc
        if doc.target == 'man':
            doc.write('* %s\n' % operation_name)
        else:
            doc.write('  %s\n' % operation_name)


class OperationDocumentEventHandler(CLIDocumentEventHandler):

    def initialize(self, session):
        CLIDocumentEventHandler.initialize(self, session)
        session.register('doc-title.Operation.*', self.title)
        session.register('doc-description.Operation.*', self.description)
        session.register('doc-synopsis-start.Operation.*',
                         self.synopsis_start)
        session.register('doc-synopsis-option.Operation.*.*',
                         self.synopsis_option)
        session.register('doc-synopsis-end.Operation.*',
                         self.synopsis_end)
        session.register('doc-options-start.Operation.*', self.options)
        session.register('doc-option.Operation.*.*', self.option)
        session.register('doc-option-example.Operation.*.*',
                         self.example_shorthand)

    def build_translation_map(self):
        for param in self.operation.params:
            self.translation_map[param.name] = param.cli_name
        for operation in self.operation.service.operations:
            self.translation_map[operation.name] = operation.cli_name

    def title(self, event_name, operation, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h1(operation.cli_name)

    def description(self, event_name, operation, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Description')
        doc.include_doc_string(operation.documentation)

    def synopsis_start(self, event_name, operation, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Synopsis')
        doc.write('::\n\n')
        doc.style.indent()
        doc.write('%s\n' % operation.cli_name)

    def synopsis_option(self, event_name, operation, argument,
                        help_command, **kwargs):
        doc = help_command.doc
        option_str = argument.cli_name
        if argument.cli_type != 'boolean':
            option_str += ' <value>'
        if not argument.required:
            option_str = '[%s]' % option_str
        doc.write('%s\n' % option_str)

    def synopsis_end(self, event_name, operation, help_command, **kwargs):
        doc = help_command.doc
        doc.style.dedent()

    def options(self, event_name, operation, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Options')
        if len(operation.params) == 0:
            doc.write('*None*\n')

    def option(self, event_name, operation, argument,
               help_command, **kwargs):
        doc = help_command.doc
        doc.write('``%s`` (%s)\n' % (argument.cli_name,
                                         argument.cli_type_name))
        doc.style.indent()
        doc.include_doc_string(argument.documentation)
        doc.style.dedent()
        doc.style.new_paragraph()

    def example_shorthand(self, event_name, operation, argument,
                          help_command, **kwargs):
        doc = help_command.doc
        param = argument.argument_object
        if param.example_fn:
            doc.style.new_paragraph()
            doc.write('Shorthand Syntax::')
            doc.style.new_paragraph()
            doc.style.indent()
            doc.write(param.example_fn(param))
            doc.style.dedent()
            doc.style.new_paragraph()


        
