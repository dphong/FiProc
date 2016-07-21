# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from datetime import datetime

from ..models import Staff, SchoolMaster, Department, TravelRecord, FiStream, SignRecord
import IndexForm


class TravelApprovalForm(forms.Form):
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
    duty = forms.CharField(
        required=True,
        label=u'职务',
    )
    companionCnt = forms.IntegerField(
        required=True,
        label=u'同行人数'
    )

    def renderPage(self, request, duty, cnt):
        username = request.session['username']
        try:
            user = Staff.objects.get(username=username)
        except:
            return IndexForm.logout(request, '当前用户登陆异常')
        form = TravelApprovalForm(
            initial={'department': user.department.name, 'name': user.name, 'duty': duty, 'companionCnt': cnt}
        )
        schoolMasterList = SchoolMaster.objects.filter()
        departmentList = Department.objects.filter()
        return (form, schoolMasterList, departmentList, user)

    def getPost(self, request):
        form, schoolMasterList, departmentList, user = self.renderPage(request, '', '')
        return render(request, 'FiProcess/approvalTravel.html',
            {'form': form, 'schoolMasterList': schoolMasterList, 'departmentList': departmentList})

    def submitPost(self, request):
        try:
            record = TravelRecord.objects.get(id=request.session['TravelRecord'])
            del request.session['TravelRecord']
        except:
            messages.add_message(request, messages.ERROR, '提交审批单失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        sign = SignRecord()
        try:
            sign.signer = Staff.objects.get(id=request.POST['approvalSigner'])
        except:
            messages.add_message(request, messages.ERROR, '审批人信息异常，无法提交申请')
            return HttpResponseRedirect(reverse('index', args={''}))
        if request.POST['departmentMasterSelect'] == 'isDepartmentMaster':
            sign.stage = 'approvalSchool'
        else:
            sign.stage = 'approvalDepartment'
        stream = record.fiStream
        stream.currentStage = 'approving'
        stream.save()
        sign.stream = stream
        sign.save()
        record.approvalSign = sign
        record.save()
        messages.add_message(request, messages.SUCCESS, '审批申请成功')
        return HttpResponseRedirect(reverse('index', args={''}))

    def post(self, request):
        form, schoolMasterList, departmentList, user = self.renderPage(request, request.POST['duty'], request.POST['companionCnt'])
        record = TravelRecord()
        fiStream = FiStream()
        record.duty = request.POST['duty']
        record.companionCnt = request.POST['companionCnt']
        record.destination = request.POST['destination']
        record.reason = request.POST['travelReason']
        tp = request.POST['travelType']
        record.travelType = tp
        carPlate = None
        carDriver = None
        if tp == 'officialCar' or tp == 'selfCar':
            record.travelDescript = 'officialCarPlate:' + request.POST['officialCarPlate'] + ',officialCarDriver:' + request.POST['officialCarDriver']
            carPlate = request.POST['officialCarPlate']
            carDriver = request.POST['officialCarDriver']
        elif tp == 'else':
            record.travelDescript = request.POST['travelTypeDescript']
        else:
            record.travelDescript = ''
        try:
            record.leaveDate = request.POST['leaveDate']
            record.returnDate = request.POST['returnDate']
            try:
                datetime.strptime(request.POST['leaveDate'], '%Y-%m-%d')
            except:
                record.leaveDate = ''
                raise Exception(u'出发日期格式错误')
            try:
                datetime.strptime(request.POST['returnDate'], '%Y-%m-%d')
            except:
                record.returnDate = ''
                raise Exception(u'返回日期格式错误')
            if not self.is_valid():
                raise Exception(u'信息错误')
            try:
                fiStream.supportDept = Department.objects.get(id=request.POST['fundDepartment'])
            except:
                raise Exception(u'经费来源部门错误')
        except Exception, e:
            return render(request, 'FiProcess/approvalTravel.html',
                {'form': form, 'schoolMasterList': schoolMasterList, 'departmentList': departmentList,
                    'errorMsg': e, 'travelRecord': record, 'carPlate': carPlate, 'carDriver': carDriver,
                    'fundDeptId': int(request.POST['fundDepartment'])})
        fiStream.applicante = user
        fiStream.projectLeader = user
        fiStream.currentStage = 'unapprove'
        fiStream.streamType = 'travelApproval'
        fiStream.applyDate = datetime.now()
        fiStream.projectName = record.reason
        fiStream.save()
        record.fiStream = fiStream
        record.duty = self.cleaned_data['duty']
        record.companionCnt = self.cleaned_data['companionCnt']
        record.save()
        request.session['TravelRecord'] = record.id
        return render(request, 'FiProcess/approvalTravel.html',
            {'form': form, 'schoolMasterList': schoolMasterList, 'departmentList': departmentList,
            'travelRecord': record, 'carPlate': carPlate, 'carDriver': carDriver, 'fundDeptId': int(request.POST['fundDepartment']),
            'submitApproval': True, 'signerList': self.getSignerList(fiStream.supportDept)})

    def getSignerList(self, department):
        signList = []
        if department.secretary:
            signList.append(department.secretary)
        if department.chief:
            signList.append(department.chief)
        if len(signList) == 0:
            return None
        return signList

    def detail(self, request, fiStream):
        del request.session['streamId']
        try:
            record = TravelRecord.objects.get(fiStream__id=fiStream.id)
        except:
            messages.add_message(request, messages.ERROR, '查看审批单失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        form, schoolMasterList, departmentList, user = self.renderPage(request, record.duty, record.companionCnt)
        carPlate = None
        carDriver = None
        if record.travelType == 'officialCar' or record.travelType == 'selfCar':
            carPlate = record.travelDescript[record.travelDescript.index(':') + 1:record.travelDescript.index(',')]
            carDriver = record.travelDescript[record.travelDescript.index(','):]
            carDriver = carDriver[carDriver.index(':') + 1:]
        record.leaveDate = record.leaveDate.strftime('%Y-%m-%d')
        record.returnDate = record.returnDate.strftime('%Y-%m-%d')
        request.session['TravelRecord'] = record.id
        signer = None
        signDescript = None
        if record.approvalSign:
            signer = record.approvalSign.signer
            if record.approvalSign.signed:
                signDescript = record.approvalSign.descript
        return render(request, 'FiProcess/approvalTravel.html',
            {'form': form, 'schoolMasterList': schoolMasterList, 'departmentList': departmentList,
            'travelRecord': record, 'carPlate': carPlate, 'carDriver': carDriver, 'funDeptId': record.fiStream.supportDept.id,
            'submitApproval': True, 'signerList': self.getSignerList(record.fiStream.supportDept), 'signer': signer,
            'signDescript': signDescript})
