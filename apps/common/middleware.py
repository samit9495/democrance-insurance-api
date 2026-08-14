"""Request-ID middleware (ENH-13).

Attaches a stable id to every request (honouring an inbound ``X-Request-ID`` or
minting one), exposes it on the response header, and puts it on a thread-local
so the logging filter can stamp every line with it.
"""

from __future__ import annotations

import uuid

from apps.common.logging import request_id_var

HEADER = "X-Request-ID"


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request_id = request.headers.get(HEADER) or uuid.uuid4().hex
        request.id = request_id
        token = request_id_var.set(request_id)
        try:
            response = self.get_response(request)
        finally:
            request_id_var.reset(token)
        response[HEADER] = request_id
        return response
