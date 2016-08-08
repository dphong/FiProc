# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from datetime import datetime

from ..models import Staff, Recept, FiStream, Department, ReceptPerson, ReceptStaff, SchoolMaster, SignRecord
import IndexForm


class ReceptApprovalForm(forms.Form):
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
        username = request.session['username']
        try:
            user = Staff.objects.get(username=username)
        except:
            return IndexForm.logout(request, '当前用户登陆异常')
        form = ReceptApprovalForm(
            initial={'applyDate': datetime.now().strftime('%Y-%m-%d'), 'workId': user.workId, 'name': user.name}
        )
        return render(request, 'FiProcess/approvalRecept.html', {'form': form, 'myDept': user.department.id, 'departmentList': Department.objects.filter()})

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
            errorMsg.append('申请日期格式错误')
        try:
            stream.department = Department.objects.get(id=request.POST['department'])
        except:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        stream.stage = 'unapprove'
        stream.projectName = request.POST['receptReason']
        stream.descript = ''
        stream.streamType = 'receptApproval'
        recept = Recept()
        recept.person = request.POST['name']
        recept.company = request.POST['department']
        recept.date = request.POST['receptDate']
        try:
            datetime.strptime(recept.date, '%Y-%m-%d')
        except:
            errorMsg.append(u'接待日期格式错误')
        recept.target = request.POST['receptPerson']
        recept.position = request.POST['receptPosition']
        recept.standard = request.POST['receptStandard']
        i = 1
        personList = []
        while('recept_name' + str(i)) in request.POST:
            person = ReceptPerson()
            person.name = request.POST['recept_name' + str(i)]
            person.position = request.POST['recept_pos' + str(i)]
            person.duty = request.POST['recept_duty' + str(i)]
            person.company = request.POST['recept_com' + str(i)]
            personList.append(person)
            i = i + 1
        i = 1
        staffList = []
        while('staff_name' + str(i)) in request.POST:
            staff = ReceptStaff()
            staff.duty = request.POST['staff_duty' + str(i)]
            try:
                staff.staff = Staff.objects.get(workId=request.POST['staff_workId' + str(i)])
                if staff.staff.name != request.POST['staff_name' + str(i)]:
                    errorMsg.append(u'第' + str(i) + u'条学校参加人员工号姓名不匹配')
            except:
                errorMsg.append(u'第' + str(i) + u'条学校参加人员工号错误')
            staffList.append(staff)
            i = i + 1
        if len(errorMsg) > 0:
            return render(request, 'FiProcess/approvalRecept.html',
                {'form': self, 'myDept': int(request.POST['department']), 'departmentList': Department.objects.filter(),
                    'recept': recept, 'stream': stream, 'personList': personList, 'staffList': staffList,
                    'errorMsg': errorMsg})
        stream.applyDate = datetime.strptime(stream.applyDate, '%Y-%m-%d')
        stream.save()
        request.session['streamId'] = stream.id
        recept.stream = stream
        recept.date = datetime.strptime(recept.date, '%Y-%m-%d')
        recept.save()
        for person in personList:
            person.recept = recept
            person.save()
        for staff in staffList:
            staff.recept = recept
            staff.save()
        return self.renderCreatedForm(request, self, recept, personList, staffList)

    def renderCreatedForm(self, request, form, recept, personList, staffList):
        form.fields['applyDate'].widget.attrs['readonly'] = True
        form.fields['workId'].widget.attrs['readonly'] = True
        form.fields['name'].widget.attrs['readonly'] = True
        signList = SignRecord.objects.filter(stream__id=recept.stream.id)
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
                if sign.stage == 'approvalDepartment':
                    deptSign = sign
                if sign.stage == 'approvalOffice':
                    superViser = sign
                if sign.stage == 'approvalSchool':
                    schoolMasters = sign
                if recept.stream.stage == sign.stage:
                    currentSigner = sign
                if sign.signed:
                    unsigned = False
        return render(request, 'FiProcess/approvalRecept.html',
            {'form': form, 'created': True, 'recept': recept, 'stream': recept.stream, 'personList': personList, 'staffList': staffList,
                'superViser': superViser, 'schoolMaster': schoolMasters, 'currentSign': currentSigner, 'deptSign': deptSign,
                'signList': signList, 'unsigned': unsigned})

    def detail(self, request, stream):
        try:
            recept = Recept.objects.get(stream__id=stream.id)
        except:
            messages.add_message(request, messages.ERROR, u'查找失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        personList = ReceptPerson.objects.filter(recept__id=recept.id)
        staffList = ReceptStaff.objects.filter(recept__id=recept.id)
        form = ReceptApprovalForm(
            initial={'applyDate': stream.applyDate.strftime('%Y-%m-%d'), 'workId': stream.applicante.workId,
                'name': recept.person}
        )
        recept.date = recept.date.strftime('%Y-%m-%d')
        return self.renderCreatedForm(request, form, recept, personList, staffList)

    def submitPost(self, request, stream):
        try:
            deptMsId = request.POST['departmentMaster']
            superViserId = request.POST['superViser']
            schoolMsId = request.POST['schoolMaster']
            deptMs = Staff.objects.get(id=deptMsId)
            superViser = Staff.objects.get(id=superViserId)
            schoolMs = Staff.objects.get(id=schoolMsId)
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
        stream.stage = 'approvalDepartment'
        stream.save()
        messages.add_message(request, messages.SUCCESS, u'提交成功')
        return HttpResponseRedirect(reverse('index', args={''}))

    def printStream(self, request, stream):
        try:
            recept = Recept.objects.get(stream__id=stream.id)
        except:
            messages.add_message(request, messages.ERROR, u'打印失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        signList = SignRecord.objects.filter(stream__id=stream.id)
        deptSign = None
        superViserSign = None
        schoolSign = None
        for sign in signList:
            if sign.stage == "approvalSchool":
                schoolSign = sign
            if sign.stage == "approvalDepartment":
                deptSign = sign
            if sign.stage == 'approvalOffice':
                superViserSign = sign
        rawPersonList = ReceptPerson.objects.filter(recept__id=recept.id)
        staffList = ReceptStaff.objects.filter(recept__id=recept.id)
        staffString = ''
        i = 0
        for staff in staffList:
            i += 1
            staffString += staff.staff.name + u'，'
            if i % 5 == 0:
                staffString += '\n'
        person = None
        personList = None
        if len(rawPersonList) <= 5:
            person = rawPersonList
        else:
            person = rawPersonList[:4]
            personList = rawPersonList[4:]
        return render(request, 'FiProcess/receptSheet.htm',
            {'stream': stream, 'recept': recept, 'staff': staffString,
                'person': person, 'personList': personList,
                'schoolSign': schoolSign, 'superViserSign': superViserSign, 'deptSign': deptSign})
