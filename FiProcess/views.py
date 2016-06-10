from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse

from Form.LoginForm import LoginForm
from Form.IndexForm import IndexForm
from registerForm import RegisterForm


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


def index(request, target=''):
    print target
    if len(target) > 0:
        if request.method == 'GET':
            form = IndexForm(request.GET)
            if target == "newstream":
                return form.newStreamGet(request)
            if target == "streamDetail":
                return form.streamDetailGet(request)
        if request.method == 'POST':
            form = IndexForm(request.POST)
            if target == "newstream":
                return form.newStreamPost(request)
        return HttpResponseRedirect(reverse('index', args={''}))
    if request.method == 'GET':
        form = IndexForm(request.GET)
        return form.get(request)
    if request.method == 'POST':
        form = IndexForm(request.POST)
        return form.post(request)
