from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from Form.LoginForm import LoginForm
from Form.IndexForm import IndexForm
from Form.CwcForm import CwcForm
from Form.RegisterForm import RegisterForm
from Form.CommonStreamDetail import CommonStreamDetail
from Form.CommonStreamForm import CommonStreamForm


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
            form = CommonStreamForm(request.GET)
            return form.newStreamGet(request)
        if target == "streamDetail":
            detail = CommonStreamDetail(request.GET)
            return detail.renderPage(request)
        if target == "newApproval":
            return form.newApprovalGet(request)
    if request.method == 'POST':
        if target == "newstream":
            form = CommonStreamForm(request.POST)
            return form.newStreamPost(request)
        if target == "streamDetail":
            detail = CommonStreamDetail(request.POST)
            return detail.onGetPost(request)
        if target == "newApproval":
            return form.newApprovalPost(request)
    return HttpResponseRedirect(reverse('index', args={''}))


def index(request, target=''):
    if len(target) > 0:
        indexTarget(request, target)
    if request.method == 'GET':
        form = IndexForm(request.GET)
        return form.get(request)
    if request.method == 'POST':
        form = IndexForm(request.POST)
        return form.post(request)


def cwc(request):
    if request.method == 'GET':
        form = CwcForm(request.GET)
        return form.get(request)
    if request.method == 'POST':
        form = CwcForm(request.POST)
        return form.post(request)
