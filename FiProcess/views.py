# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from Form import IndexForm
from Form.LoginForm import LoginForm
from Form.CwcForm import CwcForm
from Form.RegisterForm import RegisterForm
from Form.NewStreamForm import NewStreamForm
from Form.CommonStreamDetail import CommonStreamDetail


def error(request):
    return render_to_response('FiProcess/error.html')


def login(request):
    if request.method == 'GET':
        form = LoginForm()
        return form.get(request)
    form = LoginForm(request.POST)
    return form.post(request)


def register(request):
    if request.method == 'GET':
        form = RegisterForm()
        return form.get(request)
    form = RegisterForm()
    return form.post(request)


def indexTarget(request, target):
    if request.method == 'GET':
        if target == "newstream":
            form = NewStreamForm(request.GET)
            return form.get(request)
        if target == "streamDetail":
            detail = CommonStreamDetail(request.GET)
            return detail.get(request)
        if target == "newApproval":
            return form.newApprovalGet(request)
    if request.method == 'POST':
        if target == "newstream":
            form = NewStreamForm(request.POST)
            return form.post(request)
        if target == "streamDetail":
            detail = CommonStreamDetail(request.POST)
            return detail.post(request)
        if target == "newApproval":
            return form.newApprovalPost(request)
    return HttpResponseRedirect(reverse('index', args={''}))


def index(request, target=''):
    if 'username' not in request.session:
        return IndexForm.logout(request, u'当前用户未登录，请登录')
    if len(target) > 0:
        return indexTarget(request, target)
    if request.method == 'GET':
        form = IndexForm.IndexForm(request.GET)
        return form.get(request)
    if request.method == 'POST':
        form = IndexForm.IndexForm(request.POST)
        return form.post(request)


def cwc(request):
    if 'username' not in request.session:
        return IndexForm.logout(request, '当前用户未登录，请登录')
    if request.method == 'GET':
        form = CwcForm(request.GET)
        return form.get(request)
    if request.method == 'POST':
        form = CwcForm(request.POST)
        return form.post(request)
