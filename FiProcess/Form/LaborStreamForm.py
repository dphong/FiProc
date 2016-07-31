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
import NewStreamForm


class LaborStreamForm(ModelForm):
    class Meta:
        model = FiStream
        fields = ['applyDate', 'department', 'projectName', 'descript']
        labels = {
            'applyDate': u'报销日期',
            'department': u'经费来源所属部门',
            'projectName': u'经费来源项目名称',
        }
        field_classes = {
            'applyDate': forms.DateField,
        }

    myDepartment = forms.CharField(
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
    currentStage = forms.CharField()

    def get(self, request):
        staff = IndexForm.getStaffFromRequest(request)
        if not staff:
            return IndexForm.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        form = LaborStreamForm(
            initial={'myDepartment': staff.department.name,
                'name': staff.name, 'workId': staff.workId, 'applyDate': datetime.today().strftime('%Y-%m-%d'),
                'projectLeaderWorkId': staff.workId, 'projectLeaderName': staff.name, 'currentStage': 'create'}
        )
        return render(request, 'FiProcess/laborStream.html', {'form': form, 'departmentList': Department.objects.filter()})

    def getPayList(self, stream):
        amount = 0
        staffPayList = StaffLaborPay.objects.filter(stream__id=stream.id)
        for pay in staffPayList:
            amount += pay.amount
        hirePayList = HireLaborPay.objects.filter(stream__id=stream.id)
        for pay in hirePayList:
            amount += pay.amount
        return (amount, staffPayList, hirePayList)

    def getDetail(self, request, stream):
        if stream.stage != 'create':
            return self.post(request, stream)
        amount, staffPayList, hirePayList = self.getPayList(stream)
        form = LaborStreamForm(
            initial={'myDepartment': stream.applicante.department.name, 'projectName': stream.projectName, 'department': stream.department,
                'name': stream.applicante.name, 'workId': stream.applicante.workId, 'applyDate': stream.applyDate.strftime('%Y-%m-%d'),
                'projectLeaderWorkId': stream.projectLeader.workId, 'projectLeaderName': stream.projectLeader.name, 'currentStage': 'create'}
        )
        return render(request, 'FiProcess/laborStream.html',
            {'form': form, 'departmentList': Department.objects.filter(), 'staffPayList': staffPayList, 'hirePayList': hirePayList, 'total': amount})

    def post(self, request, stream):
        amount, staffPayList, hirePayList = self.getPayList(stream)
        if stream.stage == 'create':
            stream.stage = 'cantModify'
            stream.save()
        try:
            signList, stageInfo = NewStreamForm.getStreamStageInfo(stream)
        except:
            messages.add_message(request, messages.ERROR, '审核状态异常')
            return HttpResponseRedirect(reverse('index', args={''}))
        form = LaborStreamForm(
            initial={'myDepartment': stream.applicante.department.name, 'projectName': stream.projectName, 'department': stream.department,
                'name': stream.applicante.name, 'workId': stream.applicante.workId, 'applyDate': stream.applyDate.strftime('%Y-%m-%d'),
                'projectLeaderWorkId': stream.projectLeader.workId, 'projectLeaderName': stream.projectLeader.name,
                'projectName': stream.projectName, 'currentStage': stageInfo}
        )
        form.fields['applyDate'].widget.attrs['readonly'] = True
        form.fields['department'].widget.attrs['readonly'] = True
        form.fields['projectName'].widget.attrs['readonly'] = True
        form.fields['projectLeaderWorkId'].widget.attrs['readonly'] = True
        form.fields['projectLeaderName'].widget.attrs['readonly'] = True
        if not stream.department.chief:
            return render(request, 'FiProcess/laborStream.html',
                {'form': form, 'cantModify': True,
                    'staffPayList': staffPayList, 'hirePayList': hirePayList, 'total': amount,
                    'signList': signList, 'signErrorMsg': u'所属部门负责人不存在!'})

        sign1, sign11, sign12, schoolSign1, schoolSign2, schoolSign3, school1Id, signId, unsigned = NewStreamForm.getSigner(stream, amount, signList)
        return render(request, 'FiProcess/laborStream.html',
            {'form': form, 'cantModify': True,
                'staffPayList': staffPayList, 'hirePayList': hirePayList, 'total': amount, 'signList': signList,
                'unsigned': unsigned, 'sign1': sign1, 'sign12': sign12, 'sign11': sign11, 'schoolSigner': school1Id, 'signId': signId,
                'schoolSign1': schoolSign1, 'schoolSign2': schoolSign2, 'schoolSign3': schoolSign3})

    def postAddRow(self, request, modifyLabor=None):
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
                sptDept = Department.objects.get(id=request.POST['department'])
            except:
                messages.add_message(request, messages.ERROR, '部门信息异常')
                return HttpResponseRedirect(reverse('index', args={''}))
            stream.department = sptDept
            stream.projectLeader = staff
            stream.stage = 'create'
            stream.projectName = request.POST['projectName']
            stream.descript = ''
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
            amount, staffPayList, hirePayList = self.getPayList(stream)
            return render(request, 'FiProcess/laborStream.html',
                {'form': self, 'departmentList': Department.objects.filter(), 'type': request.POST['laborType'],
                    'pay': pay, 'errorMsg': errorMsg, 'staffPayList': staffPayList, 'hirePayList': hirePayList,
                    'total': amount})
        pay.amount = float(pay.amount)
        pay.date = datetime.strptime(pay.date, '%Y-%m-%d')
        pay.save()
        if modifyLabor:
            print modifyLabor
            modifyLabor.delete()
        return self.renderForm(request, stream)

    def postModifyRow(self, request):
        if 'staffLaborId' in request.session:
            labor = StaffLaborPay.objects.filter(id=request.session['staffLaborId'])
            del request.session['staffLaborId']
        if 'hireLaborId' in request.session:
            labor = HireLaborPay.objects.filter(id=request.session['hireLaborId'])
            del request.session['hireLaborId']
        if 'streamId' not in request.session:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        print labor
        return self.postAddRow(request, labor)

    def renderForm(self, request, stream):
        amount, staffPayList, hirePayList = self.getPayList(stream)
        return render(request, 'FiProcess/laborStream.html',
            {'form': self, 'departmentList': Department.objects.filter(), 'staffPayList': staffPayList,
            'hirePayList': hirePayList, 'total': amount})

    def laborPayExcept(self, request):
        if 'streamId' in request.session:
            try:
                stream = FiStream.objects.get(id=request.session['streamId'])
                return self.renderForm(request, stream)
            except:
                pass
        messages.add_message(request, messages.ERROR, u'操作失败')
        return HttpResponseRedirect(reverse('index', args={''}))

    def delStaffLaborPay(self, request, staffLaborId):
        try:
            labor = StaffLaborPay.objects.get(id=staffLaborId)
        except:
            return self.laborPayExcept(request)
        labor.delete()
        return self.renderForm(request, labor.stream)

    def modifyStaffLaborPay(self, request, staffLaborId):
        try:
            labor = StaffLaborPay.objects.get(id=staffLaborId)
        except:
            return self.laborPayExcept(request)
        request.session['staffLaborId'] = labor.id
        amount, staffPayList, hirePayList = self.getPayList(labor.stream)
        labor.date = labor.date.strftime('%Y-%m-%d')
        return render(request, 'FiProcess/laborStream.html',
            {'form': self, 'departmentList': Department.objects.filter(), 'type': 'staff', 'modify': True,
                'pay': labor, 'staffPayList': staffPayList, 'hirePayList': hirePayList, 'total': amount})

    def delHireLaborPay(self, request, hireLaborId):
        try:
            labor = HireLaborPay.objects.get(id=hireLaborId)
        except:
            return self.laborPayExcept(request)
        labor.delete()
        return self.renderForm(request, labor.stream)

    def modifyHireLaborPay(self, request, hireLaborId):
        try:
            labor = HireLaborPay.objects.get(id=hireLaborId)
        except:
            return self.delHireLaborPay(request)
        request.session['hireLaborId'] = labor.id
        amount, staffPayList, hirePayList = self.getPayList(labor.stream)
        labor.date = labor.date.strftime('%Y-%m-%d')
        return render(request, 'FiProcess/laborStream.html',
            {'form': self, 'departmentList': Department.objects.filter(), 'type': 'hire', 'modify': True,
                'pay': labor, 'staffPayList': staffPayList, 'hirePayList': hirePayList, 'total': amount})
