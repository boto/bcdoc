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


class CLIDocumentHandler(object):

    def __init__(self, fp=None, style=None, target='man',
                 extra_handlers=None):
        if fp is None:
            fp = cStringIO()
        self.fp = fp
        if style is None:
            style = ReSTStyle(self)
        self.style = style
        self.target = target
        self.parser = DocStringParser(self)
        self.keep_data = True
        self.do_translation = False
        self.translation_map = {}
        #self.build_translation_map()

    def initialize(self, session):
        pass

    def write(self, s):
        self.fp.write('%s%s' % (self.style.spaces(), s))

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


class ProviderDocumentHandler(CLIDocumentHandler):

    def __init__(self, fp=None, style=None):
        CLIDocumentHandler.__init__(self, fp, style)
        self._cli_data = None

    def initialize(self, session):
        CLIDocumentHandler.initialize(self, session)
        session.register('doc-title.Provider.*', self.title)
        session.register('doc-description.Provider.*', self.description)
        session.register('doc-synopsis-start.Provider.*', self.synopsis)
        session.register('doc-options-start.Provider.*', self.options)
        session.register('doc-option.Provider.*.*', self.option)
        session.register('doc-subitems-start.Provider.*', self.subitems)
        session.register('doc-subitem.Provider.*.*', self.subitem)

    def title(self, event_name, provider, help_command, **kwargs):
        self.style.h1(provider.name)

    def description(self, event_name, provider, help_command, **kwargs):
        self.style.h2('Description')
        self.include_doc_string(help_command.description)

    def synopsis(self, event_name, provider, help_command, **kwargs):
        self.style.h2('Synopsis')
        self.style.codeblock(help_command.synopsis)
        self.include_doc_string(help_command.help_usage)
        self.style.new_paragraph()

    def options(self, event_name, provider, help_command, **kwargs):
        self.style.h2('Options')

    def option(self, event_name, argument, **kwargs):
        self.write('``%s`` (%s)\n' % (argument.cli_name,
                                      argument.cli_type_name))
        self.style.indent()
        self.include_doc_string(argument.documentation)
        self.style.dedent()
        self.style.new_paragraph()
        if argument.choices:
            self.style.start_ul()
            for choice in argument.choices:
                self.style.li(choice)
            self.style.end_ul()

    def subitems(self, event_name, provider, help_command, **kwargs):
        self.style.h2('Available Services')
        self.style.toctree()

    def subitem(self, event_name, provider, service_name, **kwargs):
        if self.target == 'man':
            self.write('* %s\n' % service_name)
        else:
            self.write('  %s/index\n' % service_name)


class ServiceDocumentHandler(CLIDocumentHandler):

    def initialize(self, session):
        CLIDocumentHandler.initialize(self, session)
        session.register('doc-title.Service.*', self.title)
        session.register('doc-description.Service.*', self.description)
        session.register('doc-subitems-start.Service.*', self.subitems)
        session.register('doc-subitem.Service.*.*', self.subitem)

    def build_translation_map(self):
        for op in self.service.operations:
            self.translation_map[op.name] = op.cli_name

    def title(self, event_name, service, **kwargs):
        self.style.h1(service.endpoint_prefix)

    def description(self, event_name, service, **kwargs):
        self.style.h2('Description')
        self.include_doc_string(service.documentation)

    def subitems(self, event_name, service, **kwargs):
        self.style.h2('Available Commands')
        self.style.toctree()

    def subitem(self, event_name, service, operation_name, **kwargs):
        if self.target == 'man':
            self.write('* %s\n' % operation_name)
        else:
            self.write('  %s\n' % operation_name)


class OperationDocumentHandler(CLIDocumentHandler):

    def initialize(self, session):
        CLIDocumentHandler.initialize(self, session)
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

    def title(self, event_name, operation, **kwargs):
        self.style.h1(operation.cli_name)

    def description(self, event_name, operation, **kwargs):
        self.style.h2('Description')
        self.include_doc_string(operation.documentation)

    def synopsis_start(self, event_name, operation, **kwargs):
        self.style.h2('Synopsis')
        self.write('::\n\n')
        self.style.indent()
        self.write('%s\n' % operation.cli_name)

    def synopsis_option(self, event_name, operation, argument, **kwargs):
        option_str = argument.cli_name
        if argument.cli_type != 'boolean':
            option_str += ' <value>'
        if not argument.required:
            option_str = '[%s]' % option_str
        self.write('%s\n' % option_str)

    def synopsis_end(self, event_name, operation, **kwargs):
        self.style.dedent()

    def options(self, event_name, operation, **kwargs):
        self.style.h2('Options')
        if len(operation.params) == 0:
            self.write('*None*\n')

    def option(self, event_name, operation, argument, **kwargs):
        self.write('``%s`` (%s)\n' % (argument.cli_name,
                                         argument.cli_type_name))
        self.style.indent()
        self.include_doc_string(argument.documentation)
        self.style.dedent()
        self.style.new_paragraph()

    def example_shorthand(self, event_name, operation, argument, **kwargs):
        param = argument.argument_object
        if param.example_fn:
            self.style.new_paragraph()
            self.write('Shorthand Syntax::')
            self.style.new_paragraph()
            self.style.indent()
            self.write(param.example_fn(param))
            self.style.dedent()
            self.style.new_paragraph()


        
