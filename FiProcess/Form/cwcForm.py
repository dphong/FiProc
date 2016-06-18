# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.context import RequestContext
from django.contrib import messages


class CwcForm(forms.Form):
    def renderForm(self, request, form):
        return render_to_response('FiProcess/cwc.html', RequestContext(request, {'form', form}))

    def get(self, request):
        if 'username' not in request.session:
            messages.add_message(request, messages.ERROR, '登录状态异常!')
            return HttpResponseRedirect(reverse('login'))
        print request.GET.get('target')
        print request.GET.get('page')
        if 'username' not in request.session:
            return HttpResponseRedirect(reverse('login'))
        form = CwcForm(request.GET)
        return self.renderForm(request, form)

    def post(self, request):
        if 'username' not in request.session:
            messages.add_message(request, messages.ERROR, '登录状态异常!')
            return HttpResponseRedirect(reverse('login'))
        if 'return' in request.POST:
            return HttpResponseRedirect(reverse('index', args={''}))
        form = CwcForm(request.POST)
        return self.renderForm(request, form)
