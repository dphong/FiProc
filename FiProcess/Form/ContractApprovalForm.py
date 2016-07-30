# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from datetime import datetime

from ..models import Staff, FiStream, Department, Contract
import IndexForm


class ContractApprovalForm(forms.Form):
    applyDate = forms.CharField(
        label=u'申请日期',
    )
    workId = forms.CharField(
        label=u'经办人工号',
    )
    name = forms.CharField(
        label=u'经办人姓名姓名',
    )

    def getPost(self, request):
        username = request.session['username']
        try:
            user = Staff.objects.get(username=username)
        except:
            return IndexForm.logout(request, '当前用户登陆异常')
        form = ContractApprovalForm(
            initial={'applyDate': datetime.now().strftime('%Y-%m-%d'), 'workId': user.workId, 'name': user.name}
        )
        return render(request, 'FiProcess/approvalContract.html', {'form': form, 'myDept': user.department.id, 'departmentList': Department.objects.filter()})

    def post(self, request):
        errorMsg = []
        stream = FiStream()
        try:
            user = Staff.objects.get(workId=request.POST['workId'])
            if user.name != request.POST['name']:
                errorMsg.append(u'工号与姓名不匹配')
            elif str(user.department.id) != request.POST['department']:
                errorMsg.append(u'部门与姓名工号不匹配')
            else:
                stream.applicante = user
                stream.projectLeader = user
        except:
            errorMsg.append(u'工号查找失败')
        stream.applyDate = request.POST['applyDate']
        try:
            datetime.strptime(stream.applyDate, '%Y-%m-%d')
        except:
            errorMsg.append(u'申请日期格式错误')
        try:
            stream.department = Department.objects.get(id=request.POST['department'])
        except:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        stream.stage = 'unapprove'
        stream.projectLeader = user
        stream.projectName = request.POST['contractName']
        stream.descript = ''
        stream.streamType = 'contractApproval'
        contract = Contract()
        contract.number = request.POST['contractNumber']
        contract.target = request.POST['contractComName']
        contract.amount = request.POST['contractAmount']
        contract.projectCom = request.POST['contractDept']
        contract.lawyer = request.POST['contractLawyer']
        contract.content = request.POST['contractContent']
        try:
            float(contract.amount)
        except:
            errorMsg.append(u'合同金额格式错误')
        if len(errorMsg) > 0:
            return render(request, 'FiProcess/approvalContract.html',
                {'form': self, 'myDept': int(request.POST['department']), 'departmentList': Department.objects.filter(),
                    'stream': stream, 'contract': contract, 'errorMsg': errorMsg})
        stream.applyDate = datetime.strptime(stream.applyDate, '%Y-%m-%d')
        stream.save()
        contract.stream = stream
        contract.amount = float(contract.amount)
        contract.save()
        self.fields['applyDate'].widget.attrs['readonly'] = True
        self.fields['workId'].widget.attrs['readonly'] = True
        self.fields['name'].widget.attrs['readonly'] = True
        return render(request, 'FiProcess/approvalContract.html',
            {'form': self, 'created': True, 'stream': stream, 'contract': contract, 'department': user.department.name})

    def detail(self, request, stream):
        try:
            contract = Contract.objects.get(stream__id=stream.id)
        except:
            messages.add_message(request, messages.ERROR, u'查找失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        form = ContractApprovalForm(
            initial={'applyDate': stream.applyDate.strftime('%Y-%m-%d'), 'workId': stream.applicante.workId,
                'name': stream.applicante.name}
        )
        form.fields['applyDate'].widget.attrs['readonly'] = True
        form.fields['workId'].widget.attrs['readonly'] = True
        form.fields['name'].widget.attrs['readonly'] = True
        return render(request, 'FiProcess/approvalContract.html',
            {'form': form, 'created': True, 'stream': stream, 'contract': contract, 'department': stream.department.name})

    def submitPost(self, request):
        messages.add_message(request, messages.SUCCESS, u'提交成功')
        return HttpResponseRedirect(reverse('index', args={''}))
