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



DOC_EVENTS = {
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

def fire_event(session, event_name, *fmtargs, **kwargs):
    event = session.create_event(event_name, *fmtargs)
    session.emit(event, **kwargs)

def document_provider(session, help_command):
    provider = help_command.provider
    fire_event(session, 'doc-title', 'Provider', provider.name,
               provider=provider, help_command=help_command)
    fire_event(session, 'doc-description', 'Provider', provider.name,
               provider=provider, help_command=help_command)
    fire_event(session, 'doc-synopsis-start', 'Provider', provider.name,
               provider=provider, help_command=help_command)
    fire_event(session, 'doc-synopsis-end', 'Provider', provider.name,
               provider=provider, help_command=help_command)
    fire_event(session, 'doc-options-start', 'Provider', provider.name,
               provider=provider, help_command=help_command)
    for arg_name in help_command.arg_table:
        arg = help_command.arg_table[arg_name]
        fire_event(session,'doc-option', 'Provider', provider.name,
                   arg_name, argument=arg, help_command=help_command)
        fire_event(session, 'doc-option-example', 'Provider',
                   provider.name, arg_name, argument=arg,
                   help_command=help_command)
    fire_event(session, 'doc-options-end', 'Provider', provider.name,
               provider=provider, help_command=help_command)
    fire_event(session, 'doc-subitems-start', 'Provider', provider.name,
               provider=provider, help_command=help_command)
    for service_name in help_command.command_table.keys():
        fire_event(session, 'doc-subitem', 'Provider',
                   provider.name, service_name,
                   provider=provider, service_name=service_name,
                   help_command=help_command)
    fire_event(session, 'doc-subitems-end', 'Provider', provider.name,
               provider=provider, help_command=help_command)

def document_service(session, help_command):
    service = help_command.service
    fire_event(session, 'doc-title', 'Service', service.endpoint_prefix,
               service=service, help_command=help_command)
    fire_event(session, 'doc-description', 'Service', service.endpoint_prefix,
               service=service, help_command=help_command)
    fire_event(session, 'doc-synopsis-start', 'Service',
               service.endpoint_prefix,
               service=service, help_command=help_command)
    fire_event(session, 'doc-synopsis-end', 'Service',
               service.endpoint_prefix,
               service=service, help_command=help_command)
    fire_event(session, 'doc-options-start', 'Service',
               service.endpoint_prefix,
               service=service, help_command=help_command)
    fire_event(session, 'doc-options-end', 'Service',
               service.endpoint_prefix,
               service=service, help_command=help_command)
    fire_event(session, 'doc-subitems-start', 'Service',
               service.endpoint_prefix,
               service=service, help_command=help_command)
    for operation_name in help_command.command_table.keys():
        fire_event(session, 'doc-subitem', 'Service',
                   service.endpoint_prefix, operation_name,
                   service=service, operation_name=operation_name,
                   help_command=help_command)
    fire_event(session, 'doc-subitems-end', 'Service',
               service.endpoint_prefix,
               service=service, help_command=help_command)

def document_command(session, help_command):
    command = help_command.command
    fire_event(session, 'doc-title', 'Command', command.name,
               command=command, help_command=help_command)
    fire_event(session, 'doc-description', 'Command', command.name,
               command=command, help_command=help_command)

def document_operation(session, help_command):
    operation = help_command.operation
    fire_event(session, 'doc-title', 'Operation', operation.name,
               operation=operation, help_command=help_command)
    fire_event(session, 'doc-description', 'Operation', operation.name,
               operation=operation, help_command=help_command)
    fire_event(session, 'doc-synopsis-start', 'Operation', operation.name,
               operation=operation, help_command=help_command)
    for arg_name in help_command.arg_table:
        arg = help_command.arg_table[arg_name]
        fire_event(session, 'doc-synopsis-option', 'Operation',
                   operation.name, arg_name, operation=operation,
                   argument=arg, help_command=help_command)
    fire_event(session, 'doc-synopsis-end', 'Operation', operation.name,
               operation=operation, help_command=help_command)
    fire_event(session, 'doc-options-start', 'Operation', operation.name,
               operation=operation, help_command=help_command)
    for arg_name in help_command.arg_table:
        arg = help_command.arg_table[arg_name]
        fire_event(session, 'doc-option', 'Operation',
                   operation.name, arg_name,
                   operation=operation, argument=arg,
                   help_command=help_command)
        fire_event(session, 'doc-option-example',  'Operation',
                   operation.name, arg_name,
                   operation=operation, argument=arg,
                   param_shorthand=help_command.param_shorthand,
                   help_command=help_command)
    fire_event(session, 'doc-options-end', 'Operation', operation.name,
               operation=operation, help_command=help_command)
    fire_event(session, 'doc-examples', 'Operation',
               operation.name, operation=operation,
               help_command=help_command)


def register_events(session):
    for event_name in DOC_EVENTS:
        session.register_event(event_name,
                               DOC_EVENTS[event_name])
