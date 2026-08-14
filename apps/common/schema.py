"""drf-spectacular hooks.

The RPC routes are registered in both trailing-slash and slashless form (so the
diagram's paths work verbatim). For the schema we keep only the canonical
slash-terminated form, which also removes the operationId collisions.
"""


def drop_slashless_paths(endpoints):
    return [endpoint for endpoint in endpoints if endpoint[0].endswith("/")]
