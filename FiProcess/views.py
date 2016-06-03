from django.shortcuts import render_to_response

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
    if request.method == 'GET':
        print 'get'
        form = IndexForm(request.GET)
        return form.get(request, target)
    if request.method == 'POST':
        print 'post'
        form = IndexForm(request.GET)
        form = IndexForm(request.POST)
        return form.post(request)
