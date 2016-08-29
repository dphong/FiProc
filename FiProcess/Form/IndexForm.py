# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password
from datetime import datetime

from ..models import Staff, StaffCheck, FiStream, SignRecord, TravelRecord, Traveler, TravelRoute
from ..models import IcbcCardRecord, SpendProof
import FormPublic


class UserInfoForm(forms.Form):
    username = forms.CharField(
        label=u"用户名",
        widget=forms.TextInput(
            attrs={
                'placeholder': u'请使用6-24位字母或数字组合'
            }
        )
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
    fiCode = forms.CharField(
        label=u'职员代码',
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
    icbcCard = forms.CharField(required=False)
    ccbCard = forms.CharField(required=False)
    password = forms.CharField()
    currentTab = ""
    isCwcStaff = False


class IndexForm(forms.Form):
    def saveUserInfoForm(self, request, staff):
        userInfoForm = UserInfoForm(request.POST)
        userInfoForm.currentTab = "user"
        try:
            if not userInfoForm.is_valid():
                raise Exception(u"字段内容错误")
            if not check_password(userInfoForm.cleaned_data['password'], staff.password):
                raise Exception(u"密码错误")
        except Exception, e:
            messages.add_message(request, messages.ERROR, '保存失败:' + str(e))
            return self.render(request, userInfoForm, staff)
        staff.phoneNumber = userInfoForm.cleaned_data['phoneNumber']
        staff.icbcCard = userInfoForm.cleaned_data['icbcCard']
        staff.ccbCard = userInfoForm.cleaned_data['ccbCard']
        if staff.username != userInfoForm.cleaned_data['username']:
            staff.username = userInfoForm.cleaned_data['username']
            querySet = Staff.objects.filter(username=staff.username)
            if len(querySet) > 0:
                messages.add_message(request, messages.ERROR, '保存失败: 用户名已存在')
                return self.render(request, userInfoForm, staff)
            staff.save()
            return FormPublic.logout(request, u'请用修改后的用户名重新登录')
        staff.save()
        userInfoForm.password = ''
        messages.add_message(request, messages.SUCCESS, '保存成功')
        if staff.department.name == u'财务处':
            userInfoForm.isCwcStaff = True
        return self.render(request, userInfoForm, staff)

    def saveNewPassword(self, request, userInfoForm, staff):
        userInfoForm.currentTab = "changepsw"
        originPsw = request.POST['originPsw']
        newPsw = request.POST['changePsw']
        if not check_password(originPsw, staff.password):
            messages.add_message(request, messages.ERROR, u'保存失败: 原密码错误')
            return self.render(request, userInfoForm, staff)
        staff.password = make_password(newPsw)
        staff.save()
        messages.add_message(request, messages.SUCCESS, '保存成功')
        return self.render(request, userInfoForm, staff)

    def approveStaffCheck(self, request, userInfoForm, renderStaff):
        userInfoForm.currentTab = "staffCheck"
        toDelIdList = request.POST.getlist('userCheckId')
        querySet = StaffCheck.objects.filter(id__in=toDelIdList)
        if 'userCheckDel' in request.POST:
            for staff in querySet:
                staff.staff.delete()
        elif 'userCheckOK'in request.POST:
            querySet.delete()
        messages.add_message(request, messages.SUCCESS, '保存成功')
        return self.render(request, userInfoForm, renderStaff)

    def render(self, request, userInfoForm, staff):
        FormPublic.clearSession(request)
        if check_password(staff.workId, staff.password):
            return render(request, 'FiProcess/index.html',
                {'userInfoForm': userInfoForm, 'unCheckStaff': u'当前用户密码为默认密码，请立即修改'})
        if request.user.is_authenticated():
            return render(request, 'FiProcess/index.html', {'userInfoForm': userInfoForm, 'orderList': self.getOrderList(request),
                    'userCheckList': StaffCheck.objects.all(), 'is_sysAdmin': True})
        querySet = StaffCheck.objects.filter(staff__username__exact=request.session['username'])
        if querySet.count() > 0:
            return render(request, 'FiProcess/index.html', {'userInfoForm': userInfoForm, 'unCheckStaff': u'当前用户未通过人工审核，无法创建报销单'})
        signList = self.getSignList(request)
        if len(signList) > 0:
            return render(request, 'FiProcess/index.html',
                {'userInfoForm': userInfoForm, 'orderList': self.getOrderList(request), 'signList': signList})
        return render(request, 'FiProcess/index.html', {'userInfoForm': userInfoForm, 'orderList': self.getOrderList(request)})

    def streamStageChange(self, stream):
        if stream.stage == 'finish' or stream.stage == 'refuesd' or stream.stage == 'approved':
            return stream.stage
        querySet = SignRecord.objects.filter(stream__id=stream.id)
        stageDict = None
        finalStr = ''
        if ('receptApproval' == stream.streamType or 'contractApproval' == stream.streamType
                or ('travelApproval' == stream.streamType and 'approv' in stream.stage and 'approved' != stream.stage)):
            if len(querySet) == 0:
                return 'unapprove'
            stageDict = {'unapprove': 0, 'approvalDepartment': 1, 'approvalOffice': 2, 'approvalSchool': 3, 'approved': 4}
            finalStr = 'approved'
        elif (('travelApproval' == stream.streamType and ('approv' not in stream.stage or stream.stage == 'approved'))
                or 'labor' == stream.streamType
                or 'travel' == stream.streamType or 'common' == stream.streamType):
            if len(querySet) == 0:
                return 'create'
            stageDict = {'create': 0, 'project': 1, 'department1': 2, 'department2': 3, 'projectDepartment': 4,
                         'school1': 5, 'school2': 6, 'school3': 7, 'financial': 8, 'finish': 9}
            finalStr = 'finish'
        else:
            raise Exception(u'报销单类型错误')
        minUnsignedStage = ""
        for item in querySet:
            if not item.signed and (stageDict[item.stage] >= stageDict[stream.stage]):
                if len(minUnsignedStage) == 0 or stageDict[item.stage] < stageDict[minUnsignedStage]:
                    minUnsignedStage = item.stage
        if len(minUnsignedStage) == 0:
            minUnsignedStage = finalStr
        return minUnsignedStage

    def post(self, request):
        staff = FormPublic.getStaffFromRequest(request)
        if not staff:
            return FormPublic.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        userInfoForm = self.getUserInfoForm(request, staff)
        if "saveUserInfo" in request.POST:
            return self.saveUserInfoForm(request, staff)
        elif "changePassword" in request.POST:
            return self.saveNewPassword(request, userInfoForm, staff)
        elif "userCheckId" in request.POST:
            return self.approveStaffCheck(request, userInfoForm, staff)
        elif "newFiStream" in request.POST:
            return HttpResponseRedirect(reverse('index', args={'newstream'}))
        elif "newApproval" in request.POST:
            return HttpResponseRedirect(reverse('index', args={'newApproval'}))
        elif 'logout' in request.POST:
            return FormPublic.logout(request)

        for name, value in request.POST.iteritems():
            if name.startswith('checkStreamDetail'):
                try:
                    stream = FiStream.objects.get(id=name[17:])
                except:
                    messages.add_message(request, messages.ERROR, u'操作失败')
                    return self.render(request, userInfoForm, staff)
                request.session['streamId'] = stream.id
                return HttpResponseRedirect(reverse('index', args={'streamDetail'}))
            if name.startswith('deleteOrder'):
                try:
                    stream = FiStream.objects.get(id=name[11:])
                except:
                    messages.add_message(request, messages.ERROR, u'删除失败')
                    return self.render(request, userInfoForm, staff)
                if stream.streamType == 'travelApproval':
                    try:
                        travelRecord = TravelRecord.objects.get(fiStream__id=stream.id)
                    except:
                        stream.delete()
                        messages.add_message(request, messages.ERROR, u'查找删除审批单失败')
                        return self.render(request, userInfoForm, staff)
                    if stream.stage == 'create':
                        queryList = Traveler.objects.filter(record__id=travelRecord.id)
                        queryList.delete()
                        queryList = TravelRoute.objects.filter(record__id=travelRecord.id)
                        queryList.delete()
                        queryList = SpendProof.objects.filter(fiStream__id=stream.id)
                        queryList.delete()
                        queryList = IcbcCardRecord.objects.filter(spendProof__fiStream__id=stream.id)
                        queryList.delete()
                        stream.stage = 'approved'
                        stream.save()
                        messages.add_message(request, messages.SUCCESS, stream.projectName + u' 报销单删除成功')
                    if stream.stage == 'unapprove':
                        travelRecord.delete()
                        messages.add_message(request, messages.SUCCESS, stream.projectName + u' 审批删除成功')
                        stream.delete()
                else:
                    messages.add_message(request, messages.SUCCESS, stream.projectName + u' 报销单删除成功')
                    stream.delete()
                userInfoForm.currentTab = 'order'
                return self.render(request, userInfoForm, staff)
            if name.startswith('fiProc'):
                userInfoForm.currentTab = 'order'
                try:
                    item = FiStream.objects.get(id=name[6:])
                    if ('submitDate' not in request.POST) or ('submitHalfDay' not in request.POST):
                        raise Exception('未填写预约报销日期')
                    try:
                        time = datetime.strptime(request.POST['submitDate'], '%Y-%m-%d')
                    except:
                        raise Exception('日期格式错误，请在报销日期中填写"年-月-日"格式的日期')
                    if request.POST['submitHalfDay'] == 'morning':
                        item.cwcSubmitDate = datetime(time.year, time.month, time.day, 9, 0, 0)
                        item.number = item.cwcSubmitDate.strftime('%Y%m%d') + '0'
                    else:
                        item.cwcSubmitDate = datetime(time.year, time.month, time.day, 14, 0, 0)
                        item.number = item.cwcSubmitDate.strftime('%Y%m%d') + '1'
                    signQuery = FiStream.objects.filter(number__startswith=item.cwcSubmitDate.strftime('%Y%m%d'))
                    item.number += "%03d" % (len(signQuery) + 1)
                    item.stage = 'cwcSubmit'
                    item.save()
                    messages.add_message(request, messages.SUCCESS, u'报销预约成功')
                    return self.render(request, userInfoForm, staff)
                except Exception, e:
                    messages.add_message(request, messages.ERROR, str(e))
                    return self.render(request, userInfoForm, staff)
            if name.startswith('signRefuse'):
                try:
                    item = SignRecord.objects.get(id=name[10:])
                except:
                    messages.add_message(request, messages.ERROR, u'操作失败')
                    return self.render(request, userInfoForm, staff)
                # signed but refused
                item.signed = True
                item.refused = True
                item.descript = request.POST['refuseSignReason']
                item.signedTime = datetime.now()
                item.save()
                item.stream.stage = 'refused'
                item.stream.save()
                userInfoForm.currentTab = 'signList'
                return self.render(request, userInfoForm, staff)
            if name.startswith('signPermit'):
                if not check_password(request.POST['signOkPassword'], staff.password):
                    messages.add_message(request, messages.ERROR, u'密码错误')
                    return self.render(request, userInfoForm, staff)
                try:
                    item = SignRecord.objects.get(id=name[10:])
                except:
                    messages.add_message(request, messages.ERROR, u'操作失败')
                    return self.render(request, userInfoForm, staff)
                item.signed = True
                item.descript = request.POST['signOkDescript']
                item.signedTime = datetime.now()
                item.save()
                userInfoForm.currentTab = 'signList'
                try:
                    item.stream.stage = self.streamStageChange(item.stream)
                    item.stream.save()
                except Exception, e:
                    messages.add_message(request, messages.ERROR, str(e))
                    return self.render(request, userInfoForm, staff)
                messages.add_message(request, messages.SUCCESS, u'审核成功')
                return self.render(request, userInfoForm, staff)
            if name.startswith('createApprovalStream'):
                try:
                    stream = FiStream.objects.get(id=name[20:])
                except:
                    messages.add_message(request, messages.ERROR, u'操作失败')
                    return self.render(request, userInfoForm, staff)
                request.session['streamId'] = stream.id
                return HttpResponseRedirect(reverse('index', args={'newstream'}))
        return FormPublic.logout(request)

    def sortOrder(self, stream):
        return stream.applyDate

    typeDic = {'common': u'普通报销', 'travel': u'差旅报销', 'labor': u'劳务发放',
            'travelApproval': u'差旅审批', 'receptApproval': u'公务接待审批', 'contractApproval': u'合同审批'}

    def getOrderList(self, request):
        streamList = FiStream.objects.filter(applicante__username=request.session['username'])
        orderList = []
        stageDic = {'createFromApp': u'未提交', 'create': u'未提交', 'project': u'项目负责人审核', 'department1': u'部门负责人审核',
                    'department2': u'部门书记审核', 'projectDepartment': u'项目部门负责人审核', 'school1': u'分管校领导审核',
                    'school2': u'财务校领导审核', 'school3': u'学校书记审核', 'financial': u'财务处审核', 'finish': u'审批结束',
                    'refused': u'拒绝审批', 'cwcSubmit': u'等待财务审核', 'cwcChecking': u'财务正在审核', 'cwcpaid': u'付款完成', 'cantModify': u'未提交',
                    'unapprove': u'待审批', 'approvalDepartment': u'部门负责人审批中', 'approvalOffice': u'处室负责人审批中', 'approvalSchool': u'学校负责人审批中', 'approved': u'已审批'}
        for item in streamList:
            if item.stage == 'refused' or item.stage == 'cwcpaid' or item.stage == 'approved':
                continue
            item.applyDate = item.applyDate.strftime('%Y-%m-%d')
            item.stage = stageDic[item.stage]
            item.streamType = self.typeDic[item.streamType]
            orderList.append(item)
        return sorted(orderList, key=self.sortOrder, reverse=True)

    def getSignList(self, request):
        signQuery = SignRecord.objects.filter(signer__username__exact=request.session['username'])
        signList = []
        for item in signQuery:
            if item.stream.stage == item.stage and not item.signed:
                item.stage = self.typeDic[item.stream.streamType]
                signList.append(item)
        return signList

    def get(self, request):
        tab = request.GET.get('currentTab')
        if tab:
            request.session['currentIndexTab'] = tab
            request.session.save()
            return JsonResponse("", safe=False)
        staff = FormPublic.getStaffFromRequest(request)
        if not staff:
            return FormPublic.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        userInfoForm = self.getUserInfoForm(request, staff)
        if 'currentIndexTab' in request.session:
            userInfoForm.currentTab = request.session['currentIndexTab']
        else:
            userInfoForm.currentTab = 'order'
        return self.render(request, userInfoForm, staff)

    def getUserInfoForm(self, request, staff):
        userInfoForm = UserInfoForm(
            initial={'username': staff.username, 'name': staff.name, 'workId': staff.workId,
                     'fiCode': FormPublic.getFiCode(staff.department.id, staff.name),
                     'phoneNumber': staff.phoneNumber, 'department': staff.department.name,
                     'icbcCard': staff.icbcCard, 'ccbCard': staff.ccbCard, }
        )
        if staff.username == staff.workId:
            userInfoForm.fields['username'].widget.attrs['readonly'] = False
            userInfoForm.fields['username'].label = u'用户名可以修改为6-24位字母或数字组合，但仅能修改一次'
        else:
            userInfoForm.fields['username'].widget.attrs['readonly'] = True
            userInfoForm.fields['username'].label = u'用户名'
        if staff.department.name == u'财务处':
            userInfoForm.isCwcStaff = True
        return userInfoForm
