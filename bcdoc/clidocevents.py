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

from botocore.provider import Provider
from botocore.service import Service
from botocore.operation import Operation


class CLIDocEvents(object):

    DocEvents = {
        'doc-title': '.%s.%s',
        'doc-description': '.%s.%s',
        'doc-synopsis-start': '.%s.%s',
        'doc-synopsis-option': '.%s.%s.%s',
        'doc-synopsis-end': '.%s.%s',
        'doc-options-start': '.%s.%s',
        'doc-option': '.%s.%s.%s',
        'doc-option-example': '.%s.%s.%s',
        'doc-options-end': '.%s.%s',
        'doc-examples': '.%s.%s',
        'doc-subitems-start': '.%s.%s',
        'doc-subitem': '.%s.%s.%s',
        'doc-subitems-end': '.%s.%s',
        }

    def __init__(self, session):
        self.session = session

    def fire_event(self, event_name, *fmtargs, **kwargs):
        event = self.session.create_event(event_name, *fmtargs)
        self.session.emit(event, **kwargs)

    def document_provider(self, provider, help_command):
        self.fire_event('doc-title', 'Provider', provider.name,
                        provider=provider, help_command=help_command)
        self.fire_event('doc-description', 'Provider', provider.name,
                        provider=provider, help_command=help_command)
        self.fire_event('doc-synopsis-start', 'Provider', provider.name,
                        provider=provider, help_command=help_command)
        self.fire_event('doc-synopsis-end', 'Provider', provider.name,
                        provider=provider, help_command=help_command)
        self.fire_event('doc-options-start', 'Provider', provider.name,
                        provider=provider, help_command=help_command)
        for arg_name in help_command.arg_table:
            arg = help_command.arg_table[arg_name]
            self.fire_event('doc-option', 'Provider', provider.name,
                            arg_name, argument=arg)
            self.fire_event('doc-option-example', 'Provider',
                            provider.name, arg_name, argument=arg)
        self.fire_event('doc-options-end', 'Provider', provider.name,
                        provider=provider, help_command=help_command)
        self.fire_event('doc-subitems-start', 'Provider', provider.name,
                        provider=provider, help_command=help_command)
        for service_name in help_command.command_table.keys():
            self.fire_event('doc-subitem', 'Provider',
                            provider.name, service_name,
                            provider=provider, service_name=service_name)
        self.fire_event('doc-subitems-end', 'Provider', provider.name,
                        provider=provider, help_command=help_command)

    def document_service(self, service, help_command):
        service = help_command.service
        self.fire_event('doc-title', 'Service', service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-description', 'Service', service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-synopsis-start', 'Service',
                        service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-synopsis-end', 'Service',
                        service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-options-start', 'Service',
                        service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-options-end', 'Service',
                        service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-subitems-start', 'Service',
                        service.endpoint_prefix,
                        service=service)
        for operation_name in help_command.command_table.keys():
            self.fire_event('doc-subitem', 'Service',
                            service.endpoint_prefix, operation_name,
                            service=service, operation_name=operation_name)
        self.fire_event('doc-subitems-end', 'Service',
                        service.endpoint_prefix,
                        service=service)

    def document_operation(self, operation, help_command):
        self.fire_event('doc-title', 'Operation', operation.name,
                        operation=operation)
        self.fire_event('doc-description', 'Operation', operation.name,
                        operation=operation)
        self.fire_event('doc-synopsis-start', 'Operation', operation.name,
                        operation=operation)
        for arg_name in help_command.arg_table:
            arg = help_command.arg_table[arg_name]
            self.fire_event('doc-synopsis-option', 'Operation',
                            operation.name, arg_name,
                            operation=operation, argument=arg)
        self.fire_event('doc-synopsis-end', 'Operation', operation.name,
                        operation=operation)
        self.fire_event('doc-options-start', 'Operation', operation.name,
                        operation=operation)
        for arg_name in help_command.arg_table:
            arg = help_command.arg_table[arg_name]
            self.fire_event('doc-option', 'Operation',
                            operation.name, arg_name,
                            operation=operation, argument=arg)
            self.fire_event('doc-option-example',  'Operation',
                            operation.name, arg_name,
                            operation=operation, argument=arg,
                            param_shorthand=help_command.param_shorthand)
        self.fire_event('doc-options-end', 'Operation', operation.name,
                        operation=operation)
        self.fire_event('doc-examples', 'Operation',
                        operation.name, operation=operation)

    def register_events(self):
        for event_name in self.DocEvents:
            self.session.register_event(event_name,
                                        self.DocEvents[event_name])


def document(session, obj, **kwargs):
    doc_events = CLIDocEvents(session)
    doc_events.register_events()
    if isinstance(obj, Provider):
        doc_events.document_provider(obj, **kwargs)
    elif isinstance(obj, Service):
        doc_events.document_service(obj, **kwargs)
    elif isinstance(obj, Operation):
        doc_events.document_operation(obj, **kwargs)
