# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.template.context import RequestContext
from django.contrib import messages, auth
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime


from ..models import Staff, StaffCheck, FiStream, SignRecord
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

    def queryStaff(self, userName, password, pswWrongMsg="密码错误"):
        staff = Staff.objects.filter(username__exact=userName)
        if staff.count() > 1:
            raise Exception("用户名查询重复,请联系管理员")
        staff = Staff.objects.get(username__exact=userName)
        if not check_password(password, staff.password):
            raise Exception(pswWrongMsg)
        return staff

    def saveUserInfoForm(self, request):
        userInfoForm = UserInfoForm(request.POST)
        userInfoForm.currentTab = "user"
        try:
            if not userInfoForm.is_valid():
                raise Exception("字段内容错误")
            staff = self.queryStaff(userInfoForm.cleaned_data['username'], userInfoForm.cleaned_data['password'])
        except Exception, e:
            messages.add_message(request, messages.ERROR, '保存失败:' + str(e))
            return self.render(request, userInfoForm)
        staff.phoneNumber = userInfoForm.cleaned_data['phoneNumber']
        staff.icbcCard = userInfoForm.cleaned_data['icbcCard']
        staff.ccbCard = userInfoForm.cleaned_data['ccbCard']
        staff.save()
        userInfoForm.password = ''
        messages.add_message(request, messages.SUCCESS, '保存成功')
        return self.render(request, userInfoForm)

    def saveNewPassword(self, request):
        userInfoForm = self.getUserInfoForm(request)
        userInfoForm.currentTab = "changepsw"
        originPsw = request.POST['originPsw']
        newPsw = request.POST['changePsw']
        try:
            staff = self.queryStaff(request.session['username'], originPsw, "原密码错误")
        except Exception, e:
            messages.add_message(request, messages.ERROR, '保存失败:' + str(e))
            return self.render(request, userInfoForm)
        staff.password = make_password(newPsw)
        staff.save()
        messages.add_message(request, messages.SUCCESS, '保存成功')
        return self.render(request, userInfoForm)

    def approveStaffCheck(self, request):
        userInfoForm = self.getUserInfoForm(request)
        userInfoForm.currentTab = "staffCheck"
        toDelIdList = request.POST.getlist('userCheckId')
        querySet = StaffCheck.objects.filter(id__in=toDelIdList)
        if 'userCheckDel' in request.POST:
            for staff in querySet:
                staff.staff.delete()
        elif 'userCheckOK'in request.POST:
            querySet.delete()
        messages.add_message(request, messages.SUCCESS, '保存成功')
        return self.render(request, userInfoForm)

    def render(self, request, userInfoForm):
        if request.user.is_authenticated():
            return render_to_response('FiProcess/index.html',
                RequestContext(request, {'userInfoForm': userInfoForm,
                    'orderList': self.getOrderList(request),
                    'userCheckList': StaffCheck.objects.all(), 'is_sysAdmin': True}))
        querySet = StaffCheck.objects.filter(staff__username__exact=request.session['username'])
        if querySet.count() > 0:
            return render_to_response('FiProcess/index.html',
                RequestContext(request, {'userInfoForm': userInfoForm, 'unCheckStaff': True}))
        signList = self.getSignList(request)
        if len(signList) > 0:
            return render_to_response('FiProcess/index.html',
                RequestContext(request, {'userInfoForm': userInfoForm,
                    'orderList': self.getOrderList(request), 'signList': signList}))
        return render_to_response('FiProcess/index.html',
            RequestContext(request, {'userInfoForm': userInfoForm,
                'orderList': self.getOrderList(request)}))

    def streamStageChange(self, stream):
        querySet = SignRecord.objects.filter(stream__id=stream.id)
        if len(querySet) == 0:
            return 'create'
        if stream.currentStage == 'finish' or stream.currentStage == 'refuesd':
            return stream.currentStage
        stageDict = {'create': 0, 'project': 1, 'department1': 2, 'department2': 3,
                     'projectDepartment': 4, 'school1': 5, 'school2': 6, 'school3': 7,
                     'financial': 8, 'finish': 9}
        minUnsignedStage = ""
        for item in querySet:
            if item.signed and (stageDict[item.stage] > stageDict[stream.currentStage]):
                raise Exception(u"审批状态异常")
            if not item.signed and (stageDict[item.stage] > stageDict[stream.currentStage]):
                if len(minUnsignedStage) == 0 or stageDict[item.stage] < stageDict[minUnsignedStage]:
                    minUnsignedStage = item.stage
        if len(minUnsignedStage) == 0:
            minUnsignedStage = 'finish'
        return minUnsignedStage

    def post(self, request):
        if "saveUserInfo" in request.POST:
            return self.saveUserInfoForm(request)
        elif "changePassword" in request.POST:
            return self.saveNewPassword(request)
        elif "userCheckId" in request.POST:
            return self.approveStaffCheck(request)
        elif "newFiStream" in request.POST:
            return HttpResponseRedirect(reverse('index', args={'newstream'}))
        elif "cwc" in request.POST:
            return HttpResponseRedirect(reverse('cwc'))
        username = request.session['username']
        querySet = FiStream.objects.filter(applicante__username=username)
        userInfoForm = self.getUserInfoForm(request)
        for item in querySet:
            if ("order" + str(item.id)) in request.POST:
                request.session['orderId'] = item.id
                return HttpResponseRedirect(reverse('index', args={'streamDetail'}))
            if ("delOrder" + str(item.id)) in request.POST:
                item.delete()
                if 'orderId' in request.session:
                    del request.session['orderId']
                messages.add_message(request, messages.SUCCESS, item.projectName + u'报销单删除成功')
                userInfoForm.currentTab = 'order'
                return self.render(request, userInfoForm)
            if ("fiProc" + str(item.id)) in request.POST:
                userInfoForm.currentTab = 'order'
                try:
                    if ('submitDate' not in request.POST) or ('submitHalfDay' not in request.POST):
                        raise Exception('未填写预约报销日期')
                    try:
                        time = datetime.strptime(request.POST['submitDate'], '%Y-%m-%d')
                    except:
                        raise Exception('日期格式错误，请在报销日期中填写"年-月-日"格式的日期')
                    if request.POST['submitHalfDay'] == 'morning':
                        item.cwcSumbitDate = datetime(time.year, time.month, time.day, 9, 0, 0)
                    else:
                        item.cwcSumbitDate = datetime(time.year, time.month, time.day, 14, 0, 0)
                    item.save()
                    messages.add_message(request, messages.SUCCESS, u'报销预约成功')
                    return self.render(request, userInfoForm)
                except Exception, e:
                    messages.add_message(request, messages.ERROR, str(e))
                    return self.render(request, userInfoForm)
        querySet = SignRecord.objects.filter(signer__username__exact=username)
        for item in querySet:
            if ("sign" + str(item.id)) in request.POST:
                request.session['signId'] = item.id
                return HttpResponseRedirect(reverse('index', args={'streamDetail'}))
            if ("refuseSign" + str(item.id)) in request.POST:
                item.signed = True
                item.refused = True
                item.discript = request.POST['refuseSignReason']
                item.save()
                item.stream.currentStage = 'refused'
                item.stream.save()
                userInfoForm.currentTab = 'signList'
                return self.render(request, userInfoForm)
            if ("signOk" + str(item.id)) in request.POST:
                item.signed = True
                item.discript = request.POST['signOkDiscript']
                item.save()
                userInfoForm.currentTab = 'signList'
                try:
                    item.stream.currentStage = self.streamStageChange(item.stream)
                    item.stream.save()
                except Exception, e:
                    messages.add_message(request, messages.ERROR, str(e))
                    return self.render(request, userInfoForm)
                messages.add_message(request, messages.SUCCESS, u'报销单审核成功')
                return self.render(request, userInfoForm)
        return self.logout(request)

    def sortOrder(self, stream):
        return stream.applyDate

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
            elif item.currentStage == 'refused':
                item.currentStage = u'拒绝审批'
            orderList.append(item)
        return sorted(orderList, key=self.sortOrder, reverse=True)

    def getSignList(self, request):
        signQuery = SignRecord.objects.filter(signer__username__exact=request.session['username'])
        signList = []
        for item in signQuery:
            if item.stream.currentStage == item.stage and not item.signed:
                signList.append(item)
        return signList

    def get(self, request):
        if 'orderId' in request.session:
            del request.session['orderId']
        if 'username' not in request.session:
            messages.add_message(request, messages.ERROR, '登录失败!')
            return HttpResponseRedirect(reverse('login'))
        userInfoForm = self.getUserInfoForm(request)
        return self.render(request, userInfoForm)

    def getStaffFromRequest(self, request):
        username = request.session['username']
        staff = Staff.objects.filter(username__exact=username)
        if not staff or staff.count() > 1:
            return None
        staff = Staff.objects.get(username__exact=username)
        return staff

    def getUserInfoForm(self, request):
        staff = self.getStaffFromRequest(request)
        if not staff:
            return self.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        userInfoForm = UserInfoForm(
            initial={'username': staff.username, 'name': staff.name, 'workId': staff.workId,
                     'phoneNumber': staff.phoneNumber, 'department': staff.department.name,
                     'icbcCard': staff.icbcCard, 'ccbCard': staff.ccbCard, }
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
        detail = CommonStreamDetail(request.POST)
        return detail.onGetPost(request)
