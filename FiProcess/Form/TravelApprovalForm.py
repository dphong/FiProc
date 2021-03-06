# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from datetime import datetime

from ..models import Staff, SchoolMaster, Department, TravelRecord, FiStream, SignRecord
import FormPublic


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

    def getPost(self, request):
        username = request.session['username']
        try:
            user = Staff.objects.get(username=username)
        except:
            return FormPublic.logout(request, '当前用户登陆异常')
        form = TravelApprovalForm(
            initial={'department': user.department.name, 'name': user.name}
        )
        schoolMasterList = SchoolMaster.objects.filter(duty__startswith='school')
        departmentList = Department.objects.filter()
        return render(request, 'FiProcess/approvalTravel.html',
            {'form': form, 'schoolMasterList': schoolMasterList, 'departmentList': departmentList})

    def submitPost(self, request):
        try:
            record = TravelRecord.objects.get(id=request.session['TravelRecord'])
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
        stream.stage = sign.stage
        stream.save()
        sign.stream = stream
        sign.save()
        record.approvalSign = sign
        record.save()
        messages.add_message(request, messages.SUCCESS, '审批申请成功')
        return HttpResponseRedirect(reverse('index', args={''}))

    def post(self, request):
        username = request.session['username']
        try:
            user = Staff.objects.get(username=username)
        except:
            return FormPublic.logout(request, '当前用户登陆异常')
        form = TravelApprovalForm(
            initial={'department': user.department.name, 'name': user.name,
                     'duty': request.POST['duty'], 'companionCnt': request.POST['companionCnt']}
        )
        schoolMasterList = SchoolMaster.objects.filter(duty__startswith='school')
        departmentList = Department.objects.filter()
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
                fiStream.department = Department.objects.get(id=request.POST['fundDepartment'])
            except:
                raise Exception(u'经费来源部门错误')
        except Exception, e:
            return render(request, 'FiProcess/approvalTravel.html',
                {'form': form, 'schoolMasterList': schoolMasterList, 'departmentList': departmentList,
                    'errorMsg': e, 'travelRecord': record, 'carPlate': carPlate, 'carDriver': carDriver,
                    'fundDeptId': int(request.POST['fundDepartment'])})
        fiStream.applicante = user
        fiStream.projectLeader = user
        fiStream.stage = 'unapprove'
        fiStream.streamType = 'travelApproval'
        fiStream.applyDate = datetime.now()
        fiStream.projectName = record.reason
        fiStream.descript = record.reason
        fiStream.save()
        record.fiStream = fiStream
        record.approveDate = datetime.now()
        record.companionCnt = self.cleaned_data['companionCnt']
        record.travelGrant = 0
        record.foodGrant = 0
        record.save()
        request.session['TravelRecord'] = record.id
        request.session['streamId'] = fiStream.id
        return render(request, 'FiProcess/approvalTravel.html',
            {'form': form, 'schoolMasterList': schoolMasterList, 'departmentList': departmentList,
            'travelRecord': record, 'carPlate': carPlate, 'carDriver': carDriver, 'fundDeptId': int(request.POST['fundDepartment']),
            'submitApproval': True, 'signerList': self.getSignerList(fiStream.department)})

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
        try:
            record = TravelRecord.objects.get(fiStream__id=fiStream.id)
        except:
            messages.add_message(request, messages.ERROR, '查看审批单失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        form = TravelApprovalForm(
            initial={'department': fiStream.applicante.department.name, 'name': fiStream.applicante.name,
                     'duty': record.duty, 'companionCnt': record.companionCnt}
        )
        schoolMasterList = SchoolMaster.objects.filter(duty__startswith='school')
        departmentList = Department.objects.filter()
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
            'travelRecord': record, 'carPlate': carPlate, 'carDriver': carDriver, 'funDeptId': record.fiStream.department.id,
            'submitApproval': True, 'signerList': self.getSignerList(record.fiStream.department), 'signer': signer,
            'signDescript': signDescript, 'fundDeptId': record.fiStream.department.id})
