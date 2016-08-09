"""FiProc URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
# from django.views.generic.base import RedirectView
import FiProcess.views

# favicon_view = RedirectView.as_view(url='/static/FiProcess/images/favicon.ico', permanent=True)

urlpatterns = [
    url(r'^hftcCsFiProcAdmin/', admin.site.urls),
    url(r'^$', FiProcess.views.login, name='login'),
    url(r'register/', FiProcess.views.register, name='register'),
    url(r'^error/', FiProcess.views.error, name='error'),
    url(r'^index/(?P<target>[a-zA-Z]*)$', FiProcess.views.index, name='index'),
    url(r'^index/(?P<target>[0-9]*)$', FiProcess.views.printStream, name='printStream'),
    url(r'^captcha/', include('captcha.urls')),
    url(r'^cwc/$', FiProcess.views.cwc, name='cwc'),
    url(r'^history/$', FiProcess.views.history, name='history'),
    # url(r'^favicon\.ico$', favicon_view),
]
