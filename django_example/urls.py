from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    url(r'^$', 'django_example.views.home', name='home'),
    # url(r'^django_example/', include('django_example.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)

if settings.DEBUG:
    print '^'+settings.STATIC_URL_REL+'version-[^/]+/(?P<path>.*)$'
    print settings.STATIC_ROOT
    print '^'+settings.STATIC_URL_REL+'(?P<path>.*)$'

    urlpatterns += patterns('',
        (r'^'+settings.STATIC_URL_REL+'version-[^/]+/(?P<path>.*)$', \
                'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
        (r'^'+settings.STATIC_URL_REL+'(?P<path>.*)$', \
                'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )
