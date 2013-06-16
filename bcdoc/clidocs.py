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

    def __init__(self, fp=None, style=None, target='man'):
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
                self.fp.write(data)
            except UnicodeEncodeError:
                self.fp.write(data.encode('utf-8'))

    def include_doc_string(self, doc_string):
        if doc_string:
            self.parser.feed(doc_string)


class ProviderDocumentHandler(CLIDocumentHandler):

    def __init__(self, fp=None, style=None):
        CLIDocumentHandler.__init__(self, fp, style)
        self._cli_data = None

    def initialize(self, session):
        session.register('doc-title.Provider.*', self.title)
        session.register('doc-description.Provider.*', self.description)
        session.register('doc-synopsis.Provider.*', self.synopsis)
        session.register('doc-options.Provider.*', self.options)
        session.register('doc-subitems.Provider.*', self.subitems)
        session.register('doc-subitem.Provider.*.*', self.subitem)

    def get_cli_data(self, session):
        if self._cli_data is None:
            self._cli_data = session.get_data('cli')
            for option in self._cli_data['options']:
                if option.startswith('--'):
                    option_data = self._cli_data['options'][option]
                    if 'choices' in option_data:
                        choices = option_data['choices']
                        if not isinstance(choices, list):
                            cp = choices.format(provider=session.provider.name)
                            choices = session.get_data(cp)
                            option_data['choices'] = choices
        return self._cli_data

    def title(self, event_name, provider, **kwargs):
        self.style.h1(provider.name)

    def description(self, event_name, provider, **kwargs):
        self.style.h2('Description')
        cli_data = self.get_cli_data(provider.session)
        self.include_doc_string(cli_data['description'])

    def synopsis(self, event_name, provider, **kwargs):
        self.style.h2('Synopsis')
        cli_data = self.get_cli_data(provider.session)
        self.style.codeblock(cli_data['synopsis'])
        self.include_doc_string(cli_data['help_usage'])
        self.style.new_paragraph()

    def options(self, event_name, provider, **kwargs):
        self.style.h2('Options')
        cli_data = self.get_cli_data(provider.session)
        for option in cli_data['options']:
            if option.startswith('--'):
                option_data = cli_data['options'][option]
                usage_str = option
                if 'metavar' in option_data:
                    usage_str += ' <%s>' % option_data['metavar']
                self.style.code(usage_str)
                if 'help' in option_data:
                    self.include_doc_string(option_data['help'])
                self.style.new_paragraph()
                if 'choices' in option_data:
                    self.style.start_ul()
                    choices = option_data['choices']
                    for choice in sorted(choices):
                        self.style.li(choice)
                    self.style.end_ul()
        self.style.new_paragraph()

    def subitems(self, event_name, provider, **kwargs):
        self.style.h2('Available Services')
        self.style.toctree()

    def subitem(self, event_name, provider, service, **kwargs):
        if self.target == 'man':
            self.fp.write('* %s\n' % service.service_full_name)
        else:
            self.fp.write('  %s/index\n' % service.endpoint_prefix)


class ServiceDocumentHandler(CLIDocumentHandler):

    def initialize(self, session):
        session.register('doc-title.Service.*', self.title)
        session.register('doc-description.Service.*', self.description)
        session.register('doc-subitems.Service.*', self.subitems)
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

    def subitem(self, event_name, service, operation, **kwargs):
        if self.target == 'man':
            self.fp.write('* %s\n' % operation.cli_name)
        else:
            self.fp.write('  %s\n' % operation.cli_name)


class OperationDocumentHandler(CLIDocumentHandler):

    def initialize(self, session):
        session.register('doc-title.Operation.*', self.title)
        session.register('doc-description.Operation.*', self.description)
        session.register('doc-synopsis.Operation.*', self.synopsis)
        session.register('doc-synopsis-option.Operation.*.*',
                         self.synopsis_option)
        session.register('doc-options.Operation.*', self.options)
        session.register('doc-option.Operation.*.*', self.option)
        #session.register('doc-examples.Operation.*', self.examples)

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

    def synopsis(self, event_name, operation, **kwargs):
        self.style.h2('Synopsis')
        self.fp.write('::\n\n')
        self.fp.write('  %s\n' % operation.cli_name)

    def synopsis_option(self, event_name, operation, parameter, **kwargs):
        option_str = parameter.cli_name
        if parameter.type != 'boolean':
            option_str += ' <value>'
        if not parameter.required:
            option_str = '[%s]' % option_str
        self.fp.write('    %s\n' % option_str)

    def options(self, event_name, operation, **kwargs):
        self.style.h2('Options')
        if len(operation.params) == 0:
            self.fp.write('*None*\n')

    def option(self, event_name, operation, parameter, **kwargs):
        self.fp.write('``%s`` (%s)\n' % (parameter.cli_name, parameter.type))
        self.style.indent()
        self.include_doc_string(parameter.documentation)
        self.style.dedent()
        self.style.new_paragraph()
