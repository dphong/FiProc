# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.forms import ModelForm
from django.template.context import RequestContext
from .models import Stuff


class RegisterForm(ModelForm):
    class Meta:
        model = Stuff
        fields = ['username', 'name', 'workId', 'phoneNumber', 'department', 'icbcCard', 'ccbCard', 'password']

    def get(self, request):
        return render_to_response('FiProcess/register.html', RequestContext(request, {'form': self, }))

    def post(self, request):
        inst = Stuff()
        form = RegisterForm(request.POST, instance=inst)
        if form.is_valid():
            form.save()
            return render_to_response('FiProcess/login.html', RequestContext(request, {'form': form, 'register_success': True}))
        else:
            return render_to_response('FiProcess/debug.html', RequestContext(request, {'form': form, 'register_success': False}))
