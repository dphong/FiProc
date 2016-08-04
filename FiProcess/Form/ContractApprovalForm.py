# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from datetime import datetime

from ..models import Staff, FiStream, Department, Contract, SchoolMaster, SignRecord
import IndexForm


class ContractApprovalForm(forms.Form):
    applyDate = forms.CharField(
        label=u'申请日期',
    )
    workId = forms.CharField(
        label=u'经办人工号',
    )
    name = forms.CharField(
        label=u'经办人姓名',
    )

    def getPost(self, request):
        try:
            user = Staff.objects.get(username=request.session['username'])
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
        request.session['streamId'] = stream.id
        contract.stream = stream
        contract.amount = float(contract.amount)
        contract.save()
        return self.renderCreatedForm(request, self, contract)

    def renderCreatedForm(self, request, form, contract):
        form.fields['applyDate'].widget.attrs['readonly'] = True
        form.fields['workId'].widget.attrs['readonly'] = True
        form.fields['name'].widget.attrs['readonly'] = True
        signList = SignRecord.objects.filter(stream__id=contract.stream.id)
        superViser = None
        schoolMasters = None
        deptSign = None
        currentSigner = None
        unsigned = True
        if not signList:
            superViser = SchoolMaster.objects.filter(duty='superviser')
            schoolMasters = SchoolMaster.objects.filter(duty__startswith='school')
        else:
            for sign in signList:
                if sign.stage == 'approvalOffice':
                    if sign.signer.department.name == u'纪委监察室':
                        superViser = sign
                if sign.stage == 'approvalSchool':
                    schoolMasters = sign
                if sign.stage == 'approvalDepartment':
                    deptSign = sign
                if contract.stream.stage == sign.stage and not sign.signed:
                    currentSigner = sign
                if sign.signed:
                    unsigned = False
        try:
            research = Department.objects.get(name=u'科研处')
            asset = Department.objects.get(name=u'资产管理处')
            financial = Department.objects.get(name=u'财务处')
        except:
            messages.add_message(request, messages.ERROR, u'部门负责人尚未指定，请联系系统管理员')
            return HttpResponseRedirect(reverse('index', args={''}))
        return render(request, 'FiProcess/approvalContract.html',
            {'form': form, 'created': True, 'stream': contract.stream, 'contract': contract,
                'superViser': superViser, 'schoolMaster': schoolMasters, 'research': research, 'deptSign': deptSign,
                'asset': asset, 'financial': financial, 'signList': signList, 'unsigned': unsigned,
                'currentSign': currentSigner})

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
        return self.renderCreatedForm(request, form, contract)

    def submitPost(self, request, stream):
        try:
            deptMsId = request.POST['departmentMaster']
            superViserId = request.POST['superViser']
            schoolMsId = request.POST['schoolMaster']
            deptMs = Staff.objects.get(id=deptMsId)
            superViser = Staff.objects.get(id=superViserId)
            schoolMs = Staff.objects.get(id=schoolMsId)
            research = Department.objects.get(name=u'科研处')
            asset = Department.objects.get(name=u'资产管理处')
            financial = Department.objects.get(name=u'财务处')
            if not research.chief or not asset.chief or not financial.chief:
                raise Exception('')
        except:
            messages.add_message(request, messages.ERROR, u'系统异常，提交失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        deptSign = SignRecord()
        deptSign.stream = stream
        deptSign.signer = deptMs
        deptSign.stage = 'approvalDepartment'
        deptSign.save()
        superViserSign = SignRecord()
        superViserSign.stream = stream
        superViserSign.signer = superViser
        superViserSign.stage = 'approvalOffice'
        superViserSign.save()
        schoolSign = SignRecord()
        schoolSign.stream = stream
        schoolSign.signer = schoolMs
        schoolSign.stage = 'approvalSchool'
        schoolSign.save()
        financialSign = SignRecord()
        financialSign.stream = stream
        financialSign.signer = financial.chief
        financialSign.stage = 'approvalOffice'
        financialSign.save()
        researchSign = SignRecord()
        researchSign.stream = stream
        researchSign.signer = research.chief
        researchSign.stage = 'approvalOffice'
        researchSign.save()
        assetSign = SignRecord()
        assetSign.stream = stream
        assetSign.signer = asset.chief
        assetSign.stage = 'approvalOffice'
        assetSign.save()
        stream.stage = 'approvalDepartment'
        stream.save()
        messages.add_message(request, messages.SUCCESS, u'提交成功')
        return HttpResponseRedirect(reverse('index', args={''}))

    def printStream(self, request, stream):
        return render(request, 'FiProcess/commonSheet.htm', {'stream': stream})
