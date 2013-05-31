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
import sys
from .document import Document

ScalarTypes = ('string', 'integer', 'boolean', 'timestamp', 'float', 'double')


class OperationDocument(Document):

    def __init__(self, session, operation):
        self.operation = operation
        Document.__init__(self, session)

    def do_filters(self, operation):
        if hasattr(operation, 'filters'):
            self.add_paragraph().write(self.style.h2('FILTERS'))
            self.add_paragraph()
            sorted_names = sorted(operation.filters)
            for filter_name in sorted_names:
                filter_data = operation.filters[filter_name]
                self.add_paragraph().write(self.style.code(filter_name))
                self.indent()
                self.add_paragraph()
                if 'documentation' in filter_data:
                    self.help_parser.feed(filter_data['documentation'])
                if 'choices' in filter_data:
                    para = self.add_paragraph()
                    para.write('Valid Values: ')
                    choices = '|'.join(filter_data['choices'])
                    para.write(self.style.code(choices))
                self.dedent()

    def example_value_name(self, param):
        if param.type == 'string':
            if hasattr(param, 'enum'):
                choices = param.enum
                return '|'.join(['"%s"' % c for c in choices])
            else:
                return '"string"'
        elif param.type == 'boolean':
            return 'true|false'
        else:
            return '%s' % param.type

    def _do_example(self, param):
        para = self.add_paragraph()
        if param.type == 'list':
            para.write('[')
            if param.members.type in ScalarTypes:
                para.write('%s, ...' % self.example_value_name(param.members))
            else:
                self.indent()
                self._do_example(param.members)
                self.add_paragraph().write('...')
                self.dedent()
                para = self.add_paragraph()
            para.write(']')
        elif param.type == 'map':
            para.write('{')
            self.indent()
            key_string = self.example_value_name(param.keys)
            para = self.add_paragraph()
            para.write('%s: ' % key_string)
            if param.members.type in ScalarTypes:
                para.write(self.example_value_name(param.members))
            else:
                self.indent()
                self._do_example(param.members)
                self.dedent()
            self.add_paragraph().write('...')
            self.dedent()
            self.add_paragraph().write('}')
        elif param.type == 'structure':
            para.write('{')
            self.indent()
            members = []
            for i, member in enumerate(param.members):
                para = self.add_paragraph()
                if member.type in ScalarTypes:
                    para.write('"%s": %s' % (member.py_name,
                                             self.example_value_name(member)))
                elif member.type == 'structure':
                    para.write('"%s": {' % member.py_name)
                    self.indent()
                    self._do_example(member)
                    self.dedent()
                elif member.type == 'map':
                    para.write('"%s": ' % member.py_name)
                    self.indent()
                    self._do_example(member)
                    self.dedent()
                elif member.type == 'list':
                    para.write('"%s": ' % member.py_name)
                    self.indent()
                    self._do_example(member)
                    self.dedent()
                if i < len(param.members) - 1:
                    para = self.get_current_paragraph()
                    para.write(',')
            self.dedent()
            para = self.add_paragraph()
            para.write('}')

    def do_example(self, param):
        if param.type in ('list', 'structure', 'map'):
            self.session.emit('add-syntax-example.%s.%s.%s' %
                              (param.operation.service.endpoint_prefix,
                               param.operation.name, param.name),
                              operation_doc=self, param=param)
            self.indent()
            para = self.add_paragraph()
            para.write(self.style.italics('JSON Parameter Syntax'))
            para.write('::')
            self.indent()
            self.add_paragraph()
            self._do_example(param)
            self.dedent()
            self.dedent()
            self.add_paragraph()

    def build_translation_map(self):
        for param in self.operation.params:
            self.translation_map[param.name] = param.cli_name
        for operation in self.operation.service.operations:
            self.translation_map[operation.name] = operation.cli_name

    def do_parameter(self, parameter, subitem=False, substructure=False):
        if subitem:
            pname = parameter.py_name
        else:
            pname = parameter.cli_name
        para = self.add_paragraph()
        para.write(self.style.code(pname))
        ptype = parameter.type
        if parameter.type == 'list':
            if parameter.members.type in ScalarTypes:
                ptype = 'list of %s' % parameter.members.type
        if parameter.type == 'boolean' and parameter.false_name:
            para.write(' | ')
            para.write(self.style.code(parameter.false_name))
        para.write(' (%s)' % ptype)
        self.indent()
        if parameter.documentation:
            self.help_parser.feed(parameter.documentation)
        if parameter.type == 'structure':
            for param in parameter.members:
                self.do_parameter(param, subitem=True, substructure=True)
        elif parameter.type == 'list':
            if parameter.members.type not in ScalarTypes:
                self.do_parameter(parameter.members, subitem=True,
                                  substructure=substructure)
        self.dedent()
        self.add_paragraph()

    def do_parameters(self, operation):
        required = []
        optional = []
        if operation.params:
            required = [p for p in operation.params if p.required]
            optional = [p for p in operation.params if not p.required]
        self.add_paragraph().write(self.style.h2('SYNOPSIS'))
        provider_name = self.session.provider.name
        self.add_paragraph().write('::')
        self.indent()
        self.add_paragraph()
        self.add_paragraph().write('%s %s %s' % (provider_name,
                                                 operation.service.cli_name,
                                                 operation.cli_name))
        self.indent()
        for param in required:
            para = self.add_paragraph()
            para.write('%s ' % param.cli_name)
            if param.type != 'boolean':
                para.write('<value>')
            else:
                para = self.add_paragraph()
                para.write('%s ' % param.false_name)
        for param in optional:
            para = self.add_paragraph()
            para.write('[%s ' % param.cli_name)
            if param.type != 'boolean':
                para.write('<value>')
            para.write(']')
        if operation.is_streaming():
            para = self.add_paragraph()
            para.write('output_file')
        self.dedent()
        self.dedent()
        self.add_paragraph().write(self.style.h2('REQUIRED PARAMETERS'))
        for param in required:
            self.do_parameter(param)
            self.do_example(param)
        if not required:
            self.add_paragraph().write('None')
        self.add_paragraph().write(self.style.h2('OPTIONAL PARAMETERS'))
        for param in optional:
            self.do_parameter(param)
            self.do_example(param)
        if not optional:
            self.add_paragraph().write('None')
        if operation.is_streaming():
            self.add_paragraph().write(self.style.h2('POSITIONAL ARGUMENTS'))
            para = self.add_paragraph()
            para.write(self.style.code('output_file'))
            para.write(' (blob)')
            self.indent()
            self.add_paragraph().write('The output file')
            self.dedent()

    def _build_output(self, name, type_dict, lines, prefix=''):
        if not name:
            name = type_dict.get('xmlname', '')
        line = '            <listitem>\n'
        line += '                <para><phrase role="topcom">'
        line += (prefix + name)
        line += '&mdash;'
        line += '</phrase>'
        line += filter_html(type_dict.get('documentation', ''),
                            True, False)
        line += '</para>'
        line += '            </listitem>\n'
        lines.append(line)
        if type_dict['type'] == 'structure':
            sorted_keys = sorted(type_dict['members'])
            prefix = '%s%s:' % (prefix, name)
            for member in sorted_keys:
                _build_output(member, type_dict['members'][member],
                              lines, prefix)
        elif type_dict['type'] == 'list':
            prefix = '%s%s:' % (prefix, name)
            _build_output('', type_dict['members'], lines, prefix)

    def do_output(self, operation):
        if operation.output:
            for key in operation.output['members']:
                _build_output(key, operation.output['members'][key], lines)

    def build(self):
        self.do_title(self.operation.cli_name)
        self.do_description(self.operation.documentation)
        self.do_parameters(self.operation)
        self.do_filters(self.operation)


class ServiceDocument(Document):

    def __init__(self, session, service):
        self.service = service
        Document.__init__(self, session)

    def build_translation_map(self):
        for op in self.service.operations:
            self.translation_map[op.name] = op.cli_name

    def do_toc(self, service):
        self.add_paragraph().write(self.style.h2('Available Commands'))
        self.add_paragraph()
        self.add_paragraph().write('.. toctree::')
        self.indent()
        self.add_paragraph().write(':maxdepth: 1')
        self.add_paragraph().write(':titlesonly:')
        self.add_paragraph()
        op_names = [op.cli_name for op in service.operations]
        op_names = sorted(op_names)
        for op_name in op_names:
            self.add_paragraph().write(op_name)
        self.dedent()

    def do_man_toc(self, service):
        self.add_paragraph().write(self.style.h2('Available Commands'))
        self.add_paragraph()
        op_names = [op.cli_name for op in service.operations]
        op_names = sorted(op_names)
        self.style.start_ul()
        for op_name in op_names:
            self.style.start_li()
            self.get_current_paragraph().write(op_name)
            self.style.end_li()
        self.add_paragraph()

    def do_operation_summary(self, operation):
        self.indent()
        self.add_paragraph().write(self.style.ref(operation.cli_name))
        self.indent()
        self.add_paragraph()
        if operation.documentation:
            self.help_parser.feed(operation.documentation)
        self.dedent()
        self.dedent()

    def build(self, do_man=False):
        self.do_title(self.service.service_full_name)
        self.do_description(self.service.documentation)
        if do_man:
            self.do_man_toc(self.service)
        else:
            self.do_toc(self.service)


class ProviderDocument(Document):

    def do_usage(self, title):
        self.add_paragraph().write(self.style.h2('aws'))
        self.help_parser.feed(title)

    def do_synopsis(self, synopsis):
        self.add_paragraph().write('::')
        self.add_paragraph()
        self.indent()
        self.add_paragraph().write(synopsis)
        self.dedent()
        self.add_paragraph()

    def do_toc(self):
        self.add_paragraph().write(self.style.h2('Available Services'))
        self.add_paragraph().write('.. toctree::')
        self.indent()
        self.add_paragraph().write(':maxdepth: 1')
        self.add_paragraph().write(':titlesonly:')
        self.add_paragraph()
        service_names = self.session.get_available_services()
        service_names = sorted(service_names)
        for service_name in service_names:
            self.add_paragraph().write(service_name+'/index')
        self.dedent()

    def do_man_toc(self):
        self.add_paragraph().write(self.style.h2('Available Services'))
        self.add_paragraph()
        service_names = self.session.get_available_services()
        service_names = sorted(service_names)
        self.style.start_ul()
        for service_name in service_names:
            self.style.start_li()
            self.get_current_paragraph().write(service_name)
            self.style.end_li()

    def do_options(self, options):
        self.add_paragraph().write(self.style.h2('OPTIONS'))
        for option in options:
            if option.startswith('--'):
                option_data = options[option]
                para = self.add_paragraph()
                usage_str = option
                if 'metavar' in option_data:
                    usage_str += ' <%s>' % option_data['metavar']
                para.write(self.style.code(usage_str))
                if 'help' in option_data:
                    self.indent()
                    self.add_paragraph().write(option_data['help'])
                    self.dedent()
                if 'choices' in option_data:
                    choices = option_data['choices']
                    self.indent()
                    for choice in sorted(choices):
                        self.style.start_li()
                        self.get_current_paragraph().write(choice)
                        self.style.end_li()
                    self.dedent()

    def build(self, session, cli_data, do_man=False):
        self.do_title(session)
        self.do_description(cli_data['description'])
        self.do_synopsis(cli_data['synopsis'])
        self.add_paragraph()
        self.help_parser.feed(cli_data['help_usage'])
        self.add_paragraph()
        self.do_options(cli_data['options'], session)
        if do_man:
            self.do_man_toc(session)
        else:
            self.do_toc(session)


def gen_man(session, service=None, operation=None, fp=None,
            cli_data=None, do_man=True):
    """
    """
    if fp is None:
        fp = sys.stdout
    if provider:
        doc = ProviderDocument(session)
        doc.build(session, cli_data, do_man)
        doc.render(fp)
    if operation:
        doc = OperationDocument(session, operation)
        doc.build()
        doc.render(fp)
    elif service:
        doc = ServiceDocument(session, service)
        doc.build(do_man)
        doc.render(fp)
