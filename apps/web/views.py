"""The single-file demo client (REQUIREMENTS 8.4, D11).

A plain Django template — no build step, no framework — so a reviewer can walk
all seven diagram calls in a browser with nothing installed.
"""

from django.views.generic import TemplateView


class DemoView(TemplateView):
    template_name = "web/index.html"
