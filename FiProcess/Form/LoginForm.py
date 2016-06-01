# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.template.context import RequestContext


class LoginForm(forms.Form):
    username = forms.CharField(
        required=True,
        label=u"用户名",
        error_messages={'required': '请输入用户名'},
        widget=forms.TextInput(
            attrs={
                'placeholder': u"用户名",
            }
        ),
    )
    password = forms.CharField(
        required=True,
        label=u"密码",
        error_messages={'required': u'请输入密码'},
        widget=forms.PasswordInput(
            attrs={
                'placeholder': u"密码",
            }
        ),
    )

    def get(self, request):
        return render_to_response('FiProcess/login.html', RequestContext(request, {'form': self, }))

    def post(self, request):
        if self.is_valid():
            # username = request.POST.get('username', '')
            # password = request.POST.get('password', '')
            # user = auth.authenticate(username=username, password=password)
            user = None
            if user is not None and user.is_active:
                #  auth.login(request, user)
                return render_to_response('FiProcess/index.html', RequestContext(request, {'form': self, }))
            else:
                return render_to_response('FiProcess/login.html', RequestContext(request, {'form': self, 'password_is_wrong': True}))
        else:
            return render_to_response('FiProcess/login.html', RequestContext(request, {'form': self, }))

    def clean(self):
        if not self.is_valid():
            raise forms.ValidationError(u"用户名和密码为必填项")
        else:
            # cleaned_data = super(LoginForm, self).clean()
            return
