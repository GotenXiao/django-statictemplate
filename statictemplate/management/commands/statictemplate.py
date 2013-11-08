# -*- coding: utf-8 -*-
from contextlib import contextmanager, nested
from optparse import make_option

from django.conf import settings
try:
    from django.conf.urls.defaults import patterns, url, include
except ImportError:
    from django.conf.urls import patterns, url, include  # pragma: no cover
from django.core.management.base import BaseCommand
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.test.client import Client


class InvalidResponseError(Exception):
    pass


@contextmanager
def override_urlconf():
    has_old = hasattr(settings, 'ROOT_URLCONF')
    old = getattr(settings, 'ROOT_URLCONF', None)
    settings.ROOT_URLCONF = 'statictemplate.management.commands.statictemplate'
    yield
    if has_old:
        setattr(settings, 'ROOT_URLCONF', old)
    else:  # pragma: no cover
        delattr(settings, 'ROOT_URLCONF')


@contextmanager
def override_middleware():
    has_old = hasattr(settings, 'MIDDLEWARE_CLASSES')
    old = getattr(settings, 'MIDDLEWARE_CLASSES', None)
    settings.MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
    )
    yield
    if has_old:
        setattr(settings, 'MIDDLEWARE_CLASSES', old)
    else:  # pragma: no cover
        delattr(settings, 'MIDDLEWARE_CLASSES')


def make_static(template):
    with nested(override_urlconf(), override_middleware()):
        client = Client()
        response = client.get('/', {'template': template})
        if response.status_code != 200:
            raise InvalidResponseError(
                'Response code was %d, expected 200' % response.status_code
            )
        return response.content


class Command(BaseCommand):
    option_list = BaseCommand.option_list + (
        make_option(
            '--output', '-o',
            action='store',
            dest='output',
            default=None,
            help='Output to a file',
        ),
    )

    def handle(self, template, **options):
        output = make_static(template)
        if options['output'] is not None:
            with open(options['output'], 'w') as fp:
                fp.write(output)
        else:
            self.stdout.write(output)


def render(request):
    template_name = request.GET['template']
    return render_to_response(template_name, RequestContext(request))


urlpatterns = patterns('',
    url('^$', render),
    url('^others', include(settings.ROOT_URLCONF))
)
