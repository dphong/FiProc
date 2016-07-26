# -*- coding: utf-8 -*-
from django import forms
from django.forms import ModelForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from datetime import datetime

from ..models import Staff, FiStream, Department, StaffLaborPay, HireLaborPay
import IndexForm


class LaborStreamForm(ModelForm):
    class Meta:
        model = FiStream
        fields = ['applyDate', 'supportDept', 'projectName', 'streamDescript']
        labels = {
            'applyDate': u'报销日期',
            'supportDept': u'经费来源所属部门',
            'projectName': u'经费来源项目名称',
        }
        field_classes = {
            'applyDate': forms.DateField,
        }

    department = forms.CharField(
        label=u'部门',
        widget=forms.TextInput(
            attrs={
                'readonly': 'readonly'
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
    projectLeaderWorkId = forms.CharField(
        label=u'项目负责人工号',
    )
    projectLeaderName = forms.CharField(
        label=u'项目负责人'
    )

    def get(self, request):
        staff = IndexForm.getStaffFromRequest(request)
        if not staff:
            return IndexForm.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        form = LaborStreamForm(
            initial={'department': staff.department.name,
                'name': staff.name, 'workId': staff.workId, 'applyDate': datetime.today().strftime('%Y-%m-%d'),
                'projectLeaderWorkId': staff.workId, 'projectLeaderName': staff.name}
        )
        return render(request, 'FiProcess/laborStream.html', {'form': form, 'departmentList': Department.objects.filter()})

    def postAddRow(self, request):
        stream = None
        if 'streamId' in request.session:
            try:
                stream = FiStream.objects.get(id=request.session['streamId'])
            except:
                messages.add_message(request, messages.ERROR, u'操作失败')
                return HttpResponseRedirect(reverse('index', args={''}))
        else:
            stream = FiStream()
            staff = IndexForm.getStaffFromRequest(request)
            if not staff:
                return IndexForm.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
            stream.applicante = staff
            stream.applyDate = request.POST['applyDate']
            try:
                sptDept = Department.objects.get(id=request.POST['supportDept'])
            except:
                messages.add_message(request, messages.ERROR, '部门信息异常')
                return HttpResponseRedirect(reverse('index', args={''}))
            stream.supportDept = sptDept
            stream.projectLeader = staff
            stream.currentStage = 'create'
            stream.projectName = request.POST['projectName']
            stream.streamDescript = ''
            stream.streamType = 'labor'
            stream.save()
            request.session['streamId'] = stream.id
        errorMsg = []
        if request.POST['laborType'] == 'staff':
            pay = StaffLaborPay()
            pay.stream = stream
            try:
                staff = Staff.objects.get(workId=request.POST['laborWorkId'])
                pay.staff = staff
                if staff.name != request.POST['laborName']:
                    errorMsg.append(u'\n姓名与工号不匹配')
                if len(staff.ccbCard) == 0 and len(request.POST['card']) == 0:
                    errorMsg.append(u'\n工资卡号未在系统中保存，请输入')
                if len(staff.ccbCard) > 0 and len(request.POST['card']) > 0 and staff.ccbCard != request.POST['card']:
                    errorMsg.append(u'\n工资卡号与系统中保存的不一致')
            except:
                errorMsg.append(u'\n工号错误')
            pay.duty = request.POST['duty']
            pay.date = request.POST['time']
            try:
                datetime.strptime(pay.date, '%Y-%m-%d')
            except:
                errorMsg.append(u'\n日期格式错误')
            pay.reason = request.POST['project']
            pay.amount = request.POST['amount']
            pay.bankName = request.POST['bankName']
            try:
                a = float(pay.amount)
                if a == 0:
                    errorMsg.append(u'\n金额不能为0')
            except:
                errorMsg.append(u'\n应发酬金格式错误')
        elif request.POST['laborType'] == 'hire':
            pay = HireLaborPay()
            pay.stream = stream
            pay.name = request.POST['laborName']
            pay.card = request.POST['card']
            pay.belong = request.POST['laborDepartment']
            pay.bankName = request.POST['bankName']
            pay.personId = request.POST['personId']
            pay.accountName = request.POST['accountName']
            if len(pay.accountName) == 0:
                pay.accountName = pay.name
            pay.duty = request.POST['duty']
            pay.date = request.POST['time']
            try:
                datetime.strptime(pay.date, '%Y-%m-%d')
            except:
                errorMsg.append(u'\n日期格式错误')
            pay.reason = request.POST['project']
            pay.amount = request.POST['amount']
            try:
                a = float(pay.amount)
                if a == 0:
                    errorMsg.append(u'\n金额不能为0')
            except:
                errorMsg.append(u'\n应发酬金格式错误')
        if len(errorMsg):
            staffPayList = StaffLaborPay.objects.filter(stream__id=stream.id)
            hirePayList = HireLaborPay.objects.filter(stream__id=stream.id)
            return render(request, 'FiProcess/laborStream.html',
                {'form': self, 'departmentList': Department.objects.filter(), 'type': request.POST['laborType'],
                    'pay': pay, 'errorMsg': errorMsg, 'staffPayList': staffPayList, 'hirePayList': hirePayList})
        pay.amount = float(pay.amount)
        pay.date = datetime.strptime(pay.date, '%Y-%m-%d')
        pay.save()
        staffPayList = StaffLaborPay.objects.filter(stream__id=stream.id)
        hirePayList = HireLaborPay.objects.filter(stream__id=stream.id)
        return render(request, 'FiProcess/laborStream.html',
            {'form': self, 'departmentList': Department.objects.filter(), 'staffPayList': staffPayList, 'hirePayList': hirePayList})
