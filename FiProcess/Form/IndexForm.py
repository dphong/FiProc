# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.context import RequestContext
from django.contrib import messages, auth
from django.contrib.auth.hashers import check_password, make_password


from ..models import Stuff, StuffCheck, FiStream
from CommonStreamForm import CommonStreamForm
from CommonStreamDetail import CommonStreamDetail


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
    currentTab = ""


class IndexForm(forms.Form):
    def logout(self, request, message='注销成功！'):
        if request.user.is_authenticated():
            auth.logout(request)
        if request.session.get('username', ""):
            del request.session['username']
        messages.add_message(request, messages.SUCCESS, message)
        return HttpResponseRedirect(reverse('login'))

    def queryStuff(self, userName, password, pswWrongMsg="密码错误"):
        stuff = Stuff.objects.filter(username__exact=userName)
        if stuff.count() > 1:
            raise Exception("用户名查询重复,请联系管理员")
        stuff = Stuff.objects.get(username__exact=userName)
        if not check_password(password, stuff.password):
            raise Exception(pswWrongMsg)
        return stuff

    def saveUserInfoForm(self, request):
        userInfoForm = UserInfoForm(request.POST)
        userInfoForm.currentTab = "user"
        try:
            if not userInfoForm.is_valid():
                raise Exception("字段内容错误")
            stuff = self.queryStuff(userInfoForm.cleaned_data['username'], userInfoForm.cleaned_data['password'])
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

    def saveNewPassword(self, request):
        userInfoForm = self.getUserInfoForm(request)
        userInfoForm.currentTab = "changepsw"
        originPsw = request.POST['originPsw']
        newPsw = request.POST['changePsw']
        try:
            stuff = self.queryStuff(request.session['username'], originPsw, "原密码错误")
        except Exception, e:
            return render_to_response('FiProcess/index.html',
                RequestContext(request, {'userInfoForm': userInfoForm, 'saveFailedMsg': str(e)})
            )
        print 'new password is ' + newPsw
        stuff.password = make_password(newPsw)
        stuff.save()
        return render_to_response('FiProcess/index.html',
            RequestContext(request, {'userInfoForm': userInfoForm, 'saveSuccess': True})
        )

    def approveStuffCheck(self, request):
        userInfoForm = self.getUserInfoForm(request)
        userInfoForm.currentTab = "stuffCheck"
        toDelIdList = request.POST.getlist('userCheckId')
        querySet = StuffCheck.objects.filter(id__in=toDelIdList)
        if 'userCheckDel' in request.POST:
            for stuff in querySet:
                stuff.stuff.delete()
        elif 'userCheckOK'in request.POST:
            querySet.delete()
        return render_to_response('FiProcess/index.html',
            RequestContext(request, {'userInfoForm': userInfoForm,
                'userCheckList': StuffCheck.objects.all(), 'is_sysAdmin': True, 'saveSuccess': True})
        )

    def post(self, request):
        if "saveUserInfo" in request.POST:
            return self.saveUserInfoForm(request)
        elif "changePassword" in request.POST:
            return self.saveNewPassword(request)
        elif "userCheckId" in request.POST:
            return self.approveStuffCheck(request)
        elif "newFiStream" in request.POST:
            return HttpResponseRedirect(reverse('index', args={'newstream'}))
        username = request.session['username']
        querySet = FiStream.objects.filter(applicante__username=username)
        i = 1
        for item in querySet:
            if ("order" + str(i)) in request.POST:
                request.session['orderId'] = item.id
                return HttpResponseRedirect(reverse('index', args={'streamDetail'}))
            if ("delOrder" + str(i)) in request.POST:
                item.delete()
                messages.add_message(request, messages.SUCCESS, item.projectName + u'报销单删除成功')
                return HttpResponseRedirect(reverse('index', args={''}))
            i = i + 1
        return self.logout(request)

    def getOrderList(self, request):
        username = request.session['username']
        streamList = FiStream.objects.filter(applicante__username=username)
        orderList = []
        for item in streamList:
            item.applyDate = item.applyDate.strftime('%Y-%m-%d')
            if item.currentStage == 'create':
                item.currentStage = u'未提交'
            elif item.currentStage == 'project':
                item.currentStage = u'项目负责人审核'
            elif item.currentStage == 'department1':
                item.currentStage = u'部门负责人审核'
            elif item.currentStage == 'department2':
                item.currentStage = u'部门书记审核'
            elif item.currentStage == 'projectDepartment':
                item.currentStage = u'项目部门负责人审核'
            elif item.currentStage == 'school1':
                item.currentStage = u'分管校领导审核'
            elif item.currentStage == 'school2':
                item.currentStage = u'财务校领导审核'
            elif item.currentStage == 'school3':
                item.currentStage = u'学校书记审核'
            elif item.currentStage == 'financial':
                item.currentStage = u'财务处审核'
            elif item.currentStage == 'finish':
                item.currentStage = u'报销完成'
            orderList.append(item)
        return orderList

    def get(self, request):
        if 'username' not in request.session:
            messages.add_message(request, messages.ERROR, '登录失败!')
            return HttpResponseRedirect(reverse('login'))
        userInfoForm = self.getUserInfoForm(request)
        if request.user.is_authenticated():
            return render_to_response('FiProcess/index.html',
                RequestContext(request, {'userInfoForm': userInfoForm,
                    'orderList': self.getOrderList(request),
                    'userCheckList': StuffCheck.objects.all(), 'is_sysAdmin': True}))
        return render_to_response('FiProcess/index.html',
            RequestContext(request, {'userInfoForm': userInfoForm,
                'orderList': self.getOrderList(request)}))

    def getStuffFromRequest(self, request):
        username = request.session['username']
        stuff = Stuff.objects.filter(username__exact=username)
        if not stuff or stuff.count() > 1:
            return None
        stuff = Stuff.objects.get(username__exact=username)
        return stuff

    def getUserInfoForm(self, request):
        stuff = self.getStuffFromRequest(request)
        if not stuff:
            return self.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        userInfoForm = UserInfoForm(
            initial={'username': stuff.username, 'name': stuff.name, 'workId': stuff.workId,
                     'phoneNumber': stuff.phoneNumber, 'department': stuff.department.name,
                     'icbcCard': stuff.icbcCard, 'ccbCard': stuff.ccbCard, }
        )
        userInfoForm.currentTab = 'order'
        return userInfoForm

    # new process stream
    def newStreamGet(self, request):
        if 'orderId' in request.session:
            form = CommonStreamForm(request.GET)
            return form.modifyForm(request)
        return render_to_response('FiProcess/newStream.html', RequestContext(request))

    def newFiStreamType(self, request):
        streamType = request.POST['newStreamType']
        if streamType == 'common':
            form = CommonStreamForm(request.POST)
            return form.showCommonStream(request, self)
        if streamType == 'travel':
            return render_to_response('FiProcess/travelStream.html', RequestContext(request))
        if streamType == 'labor':
            return render_to_response('FiProcess/laborStream.html', RequestContext(request))
        return render_to_response('FiProcess/newStream.html', RequestContext(request))

    def newStreamPost(self, request):
        if "newStreamType" in request.POST:
            return self.newFiStreamType(request)
        if "commonStreamForm" in request.POST:
            form = CommonStreamForm(request.POST)
            return form.commonStreamPost(request, self)
        return render_to_response('FiProcess/newStream.html', RequestContext(request))

    def streamDetailGet(self, request):
        detail = CommonStreamDetail(request.GET)
        return detail.renderPage(request)

    def streamDetailPost(self, request):
        if 'returnStream' in request.POST:
            return HttpResponseRedirect(reverse('index', args={'newstream'}))
        if 'createStream' in request.POST:
            return 
        return HttpResponseRedirect(reverse('error'))
