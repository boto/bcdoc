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
        'doc-synopsis': '.%s.%s',
        'doc-synopsis-option': '.%s.%s.%s',
        'doc-options': '.%s.%s',
        'doc-option': '.%s.%s.%s',
        'doc-option-example': '.%s.%s.%s',
        'doc-examples': '.%s.%s',
        'doc-subitems': '.%s.%s',
        'doc-subitem': '.%s.%s.%s',
        }

    def __init__(self, session):
        self.session = session

    def fire_event(self, event_name, *fmtargs, **kwargs):
        event = self.session.create_event(event_name, *fmtargs)
        self.session.emit(event, **kwargs)

    def document_provider(self, provider):
        self.fire_event('doc-title', 'Provider', provider.name,
                        provider=provider)
        self.fire_event('doc-description', 'Provider', provider.name,
                        provider=provider)
        self.fire_event('doc-synopsis', 'Provider', provider.name,
                        provider=provider)
        self.fire_event('doc-options', 'Provider', provider.name,
                        provider=provider)
        self.fire_event('doc-subitems', 'Provider', provider.name,
                        provider=provider)
        for service in provider.services:
            self.fire_event('doc-subitem', 'Provider',
                            provider.name, service.endpoint_prefix,
                            provider=provider, service=service)

    def document_service(self, service):
        self.fire_event('doc-title', 'Service', service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-description', 'Service', service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-synopsis', 'Service', service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-options', 'Service', service.endpoint_prefix,
                        service=service)
        self.fire_event('doc-subitems', 'Service', service.endpoint_prefix,
                        service=service)
        for operation in service.operations:
            self.fire_event('doc-subitem', 'Service',
                            service.endpoint_prefix, operation.name,
                            service=service, operation=operation)

    def document_operation(self, operation):
        self.fire_event('doc-title', 'Operation', operation.name,
                        operation=operation)
        self.fire_event('doc-description', 'Operation', operation.name,
                        operation=operation)
        self.fire_event('doc-synopsis', 'Operation', operation.name,
                        operation=operation)
        for param in operation.params:
            self.fire_event('doc-synopsis-option', 'Operation',
                            operation.name, param.name,
                            operation=operation, parameter=param)
        self.fire_event('doc-options', 'Operation', operation.name,
                        operation=operation)
        for param in operation.params:
            self.fire_event('doc-option', 'Operation',
                            operation.name, param.name,
                            operation=operation, parameter=param)
            self.fire_event('doc-option-example',  'Operation',
                            operation.name, param.name,
                            operation=operation, parameter=param)
        self.fire_event('doc-examples', 'Operation', operation.name,
                        operation=operation)

    def register_events(self):
        for event_name in self.DocEvents:
            self.session.register_event(event_name,
                                        self.DocEvents[event_name])


def document(session, obj):
    doc_events = CLIDocEvents(session)
    doc_events.register_events()
    if isinstance(obj, Provider):
        doc_events.document_provider(obj)
    elif isinstance(obj, Service):
        doc_events.document_service(obj)
    elif isinstance(obj, Operation):
        doc_events.document_operation(obj)
