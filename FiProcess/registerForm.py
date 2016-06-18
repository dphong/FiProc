# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.forms import ModelForm
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.contrib.auth.hashers import make_password

from .models import Staff


class RegisterForm(ModelForm):
    class Meta:
        model = Staff
        fields = ['username', 'name', 'workId', 'phoneNumber', 'department', 'icbcCard', 'ccbCard', 'password']
        labels = {
            'department': u'部门'
        }
        icbcCard = forms.CharField(required=False)
        ccbCard = forms.CharField(required=False)

    def get(self, request):
        form = RegisterForm(
            initial={'username': '', 'name': '', 'workId': '', 'phoneNumber': '', 'icbcCard': '', 'ccbCard': ''}
        )
        return render_to_response('FiProcess/register.html', RequestContext(request, {'form': form, 'register_success': True}))

    def post(self, request):
        print request.POST
        inst = Staff()
        form = RegisterForm(request.POST, instance=inst)
        if 'captchaRefresh' in request.POST:
            return render_to_response('FiProcess/register.html', RequestContext(request, {'form': form}))
        if form.is_valid():
            # username and work id duplication check
            username = Staff.objects.filter(username=inst.username)
            message = ""
            if username:
                message = u"用户" + inst.username + u"已存在"
            if inst.workId != '0':
                workId = Staff.objects.filter(workId=inst.workId)
                if workId:
                    message = u"工号" + inst.workId + u"已注册"
            if len(message) > 0:
                return render_to_response('FiProcess/register.html', RequestContext(request, {'form': form, 'message': message}))
            inst.password = make_password(inst.password)
            inst.save()
            inst.staffcheck_set.create()
            messages.add_message(request, messages.INFO, inst.username)
            return HttpResponseRedirect(reverse('login'))
        else:
            print form.errors
            return render_to_response('FiProcess/register.html', RequestContext(request, {'form': form, 'register_success': False}))
