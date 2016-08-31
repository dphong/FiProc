# -*- coding: utf-8 -*-
from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from Form import FormPublic
from Form.IndexForm import IndexForm
from Form.LoginForm import LoginForm
from Form.CwcForm import CwcForm
from Form.RegisterForm import RegisterForm
from Form.NewStreamForm import NewStreamForm
from Form.ApprovalForm import ApprovalForm
from Form.PrintForm import PrintForm
from Form.HistoryForm import HistoryForm


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
            form = NewStreamForm(request.GET)
            return form.getDetail(request)
        if target == "newApproval":
            form = ApprovalForm(request.GET)
            return form.get(request)
        if target == "approvalDetail":
            form = ApprovalForm(request.GET)
            return form.getDetail(request)
    if request.method == 'POST':
        if target == "newstream":
            form = NewStreamForm(request.POST)
            return form.post(request)
        if target == "streamDetail":
            form = NewStreamForm(request.POST)
            return form.postDetail(request)
        if target == "newApproval":
            form = ApprovalForm(request.POST)
            return form.post(request)
        if target == "approvalDetail":
            form = ApprovalForm(request.POST)
            return form.postDetail(request)
    if target == "testException":
        print 'exception ' + target
        raise Exception('test')
    return HttpResponseRedirect(reverse('index', args={''}))


def index(request, target=None):
    if 'username' not in request.session:
        return FormPublic.logout(request, u'当前用户未登录，请登录')
    if target:
        return indexTarget(request, target)
    FormPublic.clearSession(request)
    if 'history' in request.session:
        return HttpResponseRedirect(reverse('history'))
    if 'office' in request.session:
        if request.session['office'] == 'cwc':
            return HttpResponseRedirect(reverse('cwc'))
        else:
            del request.session['office']
    if request.method == 'GET':
        form = IndexForm(request.GET)
        return form.get(request)
    if request.method == 'POST':
        form = IndexForm(request.POST)
        return form.post(request)
    return HttpResponseRedirect(reverse('index', args={''}))


def cwc(request):
    if 'username' not in request.session:
        return FormPublic.logout(request, '当前用户未登录，请登录')
    if request.method == 'GET':
        form = CwcForm(request.GET)
        return form.get(request)
    if request.method == 'POST':
        form = CwcForm(request.POST)
        return form.post(request)


def printStream(request, target):
    if 'username' not in request.session:
        return FormPublic.logout(request, '当前用户未登录，请登录')
    form = PrintForm()
    return form.get(request, target)


def history(request):
    if 'username' not in request.session:
        return FormPublic.logout(request, '当前用户未登录，请登录')
    if request.method == 'GET':
        form = HistoryForm(request.GET)
        return form.get(request)
    if request.method == 'POST':
        form = HistoryForm(request.POST)
        return form.post(request)
