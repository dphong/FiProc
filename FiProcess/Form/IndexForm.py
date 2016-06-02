# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.context import RequestContext
from django.contrib import messages

from ..models import Stuff


class IndexForm(forms.Form):
    def logout(self, request):
        username = request.session.get('username', "")
        if username:
            del request.session['username']
        messages.add_message(request, messages.SUCCESS, '注销成功！')
        return HttpResponseRedirect(reverse('login'))

    def post(self, request):
        return self.logout(request)

    def get(self, request):
        if not request.session['username']:
            messages.add_message(request, messages.ERROR, '登录失败!')
            return HttpResponseRedirect(reverse('login'))
        return render_to_response('FiProcess/index.html', RequestContext(request))
