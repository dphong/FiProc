# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response, render
from django.forms import ModelForm
from django.template.context import RequestContext
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.core.urlresolvers import reverse

from .models import Stuff


class RegisterForm(ModelForm):

    class Meta:
        model = Stuff
        fields = ['username', 'name', 'workId', 'phoneNumber', 'department', 'icbcCard', 'ccbCard', 'password']

    def get(self, request):
        form = RegisterForm(
            initial={'username': '', 'name': '', 'workId': '', 'phoneNumber': '', 'icbcCard': '', 'ccbCard': ''}
        )
        return render_to_response('FiProcess/register.html', RequestContext(request, {'form': form, 'register_success': True}))

    def post(self, request):
        inst = Stuff()
        form = RegisterForm(request.POST, instance=inst)
        if form.is_valid():
            # username and work id duplication check
            username = Stuff.objects.filter(username=inst.username)
            workId = Stuff.objects.filter(workId=inst.workId)
            message = ""
            if username:
                message = u"用户" + inst.username + u"已存在"
            if workId:
                message = u"工号" + inst.workId + u"已注册"
            if len(message) > 0:
                return render(request, 'FiProcess/register.html', {'form': form, 'message': message})
            inst.save()
            inst.stuffcheck_set.create()
            messages.add_message(request, messages.INFO, inst.username)
            return HttpResponseRedirect(reverse('login'))
        else:
            return render(request, 'FiProcess/register.html', {'form': form, 'register_success': False})
