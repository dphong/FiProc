# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.context import RequestContext
from django.contrib import messages, auth
from django.contrib.auth.hashers import check_password

from ..models import Stuff


class UserInfoForm(forms.Form):
    username = forms.CharField(
        label=u"用户名",
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly',
            }
        ),
    )
    name = forms.CharField(
        label=u'姓名',
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly',
            }
        ),
    )
    workId = forms.CharField(
        label=u'工号',
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly'
            }
        ),
    )
    department = forms.CharField(
        label=u'部门',
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly'
            }
        ),
    )
    phoneNumber = forms.CharField()
    icbcCard = forms.CharField()
    ccbCard = forms.CharField()
    password = forms.CharField()


class IndexForm(forms.Form):
    def logout(self, request, message='注销成功！'):
        if request.user.is_authenticated():
            auth.logout(request)
        if request.session.get('username', ""):
            del request.session['username']
        messages.add_message(request, messages.SUCCESS, message)
        return HttpResponseRedirect(reverse('login'))

    def post(self, request):
        if "saveUserInfo" in request.POST:
            userInfoForm = UserInfoForm(request.POST)
            try:
                if not userInfoForm.is_valid():
                    raise Exception("字段内容错误")
                stuff = Stuff.objects.filter(username__exact=userInfoForm.cleaned_data['username'])
                if stuff.count() > 1:
                    raise Exception("用户名查询重复,请联系管理员")
                stuff = Stuff.objects.get(username__exact=userInfoForm.cleaned_data['username'])
                if not check_password(userInfoForm.cleaned_data['password'], stuff.password):
                    raise Exception("密码错误")
            except Exception, e:
                return render_to_response('FiProcess/index.html',
                    RequestContext(request, {'userInfoForm': userInfoForm, 'saveFailedMsg': str(e)})
                )
            stuff.phoneNumber = userInfoForm.cleaned_data['phoneNumber']
            stuff.icbcCard = userInfoForm.cleaned_data['icbcCard']
            stuff.ccbCard = userInfoForm.cleaned_data['ccbCard']
            stuff.save()
            userInfoForm.password = ''
            return render_to_response('FiProcess/index.html',
                RequestContext(request, {'userInfoForm': userInfoForm, 'saveSuccess': True})
            )
        elif "changePassword" in request.POST:
            print request.POST['password']
            userInfoForm = self.getUserInfoForm(request)
            return render_to_response('FiProcess/index.html',
                RequestContext(request, {'userInfoForm': userInfoForm, 'saveSuccess': True})
            )
        return self.logout(request)

    def get(self, request, target):
        if target == 'changepsw':
            return render_to_response('FiProcess/index.html', RequestContext(request, {'changePsw': True}))
        if not request.session['username']:
            messages.add_message(request, messages.ERROR, '登录失败!')
            return HttpResponseRedirect(reverse('login'))
        if request.user.is_authenticated():
            return render_to_response('FiProcess/index.html', RequestContext(request, {'sys_admin': True}))
        userInfoForm = self.getUserInfoForm(request)
        return render_to_response('FiProcess/index.html', RequestContext(request, {'userInfoForm': userInfoForm}))

    def getUserInfoForm(self, request):
        username = request.session['username']
        stuff = Stuff.objects.filter(username__exact=username)
        if not stuff or stuff.count() > 1:
            return self.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        stuff = Stuff.objects.get(username__exact=username)
        userInfoForm = UserInfoForm(
            initial={'username': stuff.username, 'name': stuff.name, 'workId': stuff.workId,
                     'phoneNumber': stuff.phoneNumber, 'department': stuff.department.name,
                     'icbcCard': stuff.icbcCard, 'ccbCard': stuff.ccbCard, }
        )
        return userInfoForm
