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
from bcdoc.clidocevents import DOC_EVENTS

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
        self.fp.write(s)

    def writeln(self, s):
        self.fp.write('%s%s\n' % (self.style.spaces(), s))

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

    def __init__(self, help_command):
        self.help_command = help_command
        self.initialize(help_command.session, help_command.event_class)

    def initialize(self, session, event_class):
        """
        The default initialization iterates through all of the
        available document events and looks for a corresponding
        handler method defined in the object.  If it's there, that
        handler method will be registered for the all events of
        that type for the specified ``event_class``.
        """
        for event in DOC_EVENTS:
            event_handler_name = event.replace('-', '_')
            if hasattr(self, event_handler_name):
                LOG.debug('found event_handler: %s' % event_handler_name)
                event_handler = getattr(self, event_handler_name)
                format_string = DOC_EVENTS[event]
                num_args = len(format_string.split('.')) - 2
                format_args = (event_class,) + ('*',) * num_args
                event_string = event + format_string % format_args
                LOG.debug('about to register: %s' % event_string)
                session.register(event_string, event_handler)


class ProviderDocumentEventHandler(CLIDocumentEventHandler):

    def doc_title(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h1(help_command.name)

    def doc_description(self, help_command, **kwargs):
        doc = help_command.doc
        provider = help_command.obj
        doc.style.h2('Description')
        doc.include_doc_string(help_command.description)
        doc.style.new_paragraph()

    def doc_synopsis_start(self, help_command, **kwargs):
        doc = help_command.doc
        provider = help_command.obj
        doc.style.h2('Synopsis')
        doc.style.codeblock(help_command.synopsis)
        doc.include_doc_string(help_command.help_usage)

    def doc_synopsis_end(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.new_paragraph()

    def doc_options_start(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Options')

    def doc_option(self, arg_name, help_command, **kwargs):
        doc = help_command.doc
        argument = help_command.arg_table[arg_name]
        doc.writeln('``%s`` (%s)' % (argument.cli_name,
                                     argument.cli_type_name))
        doc.include_doc_string(argument.documentation)
        if argument.choices:
            doc.style.start_ul()
            for choice in argument.choices:
                doc.style.li(choice)
            doc.style.end_ul()

    def doc_subitems_start(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Available Services')
        doc.style.toctree()

    def doc_subitem(self, command_name, help_command, **kwargs):
        doc = help_command.doc
        if doc.target == 'man':
            doc.write('* %s\n' % command_name)
        else:
            doc.write('  %s/index\n' % command_name)


class ServiceDocumentEventHandler(CLIDocumentEventHandler):

    def build_translation_map(self):
        for op in self.service.operations:
            self.translation_map[op.name] = op.cli_name

    def doc_title(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h1(help_command.name)

    def doc_description(self, help_command, **kwargs):
        doc = help_command.doc
        service = help_command.obj
        doc.style.h2('Description')
        doc.include_doc_string(service.documentation)

    def doc_subitems(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Available Commands')
        doc.style.toctree()

    def doc_subitem(self, command_name, help_command, **kwargs):
        doc = help_command.doc
        if doc.target == 'man':
            doc.write('* %s\n' % command_name)
        else:
            doc.write('  %s\n' % command_name)


class OperationDocumentEventHandler(CLIDocumentEventHandler):

    def build_translation_map(self):
        for param in self.operation.params:
            self.translation_map[param.name] = param.cli_name
        for operation in self.operation.service.operations:
            self.translation_map[operation.name] = operation.cli_name

    def doc_title(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h1(help_command.name)

    def doc_description(self, help_command, **kwargs):
        doc = help_command.doc
        operation = help_command.obj
        doc.style.h2('Description')
        doc.include_doc_string(operation.documentation)

    def doc_synopsis_start(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.h2('Synopsis')
        doc.style.start_codeblock()
        doc.writeln('%s' % help_command.name)

    def doc_synopsis_option(self, arg_name, help_command, **kwargs):
        doc = help_command.doc
        argument = help_command.arg_table[arg_name]
        option_str = argument.cli_name
        if argument.cli_type != 'boolean':
            option_str += ' <value>'
        if not argument.required:
            option_str = '[%s]' % option_str
        doc.writeln('%s' % option_str)

    def doc_synopsis_end(self, help_command, **kwargs):
        doc = help_command.doc
        doc.style.end_codeblock()

    def doc_options(self, help_command, **kwargs):
        doc = help_command.doc
        operation = help_command.obj
        doc.style.h2('Options')
        if len(operation.params) == 0:
            doc.write('*None*\n')

    def doc_option(self, arg_name, help_command, **kwargs):
        doc = help_command.doc
        argument = help_command.arg_table[arg_name]
        doc.write('``%s`` (%s)\n' % (argument.cli_name,
                                     argument.cli_type_name))
        doc.style.indent()
        doc.include_doc_string(argument.documentation)
        doc.style.dedent()
        doc.style.new_paragraph()

    def doc_example_shorthand(self, arg_name, help_command, **kwargs):
        doc = help_command.doc
        argument = help_command.arg_table[arg_name]
        param = argument.argument_object
        if param.example_fn:
            doc.style.new_paragraph()
            doc.write('Shorthand Syntax')
            doc.style.start_codeblock()
            for example_line in param.example_fn(param).splitlines():
                doc.writeln(example_line)
            doc.style.end_codeblock()


        
