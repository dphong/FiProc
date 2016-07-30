# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from datetime import datetime

from ..models import Staff, Recept, FiStream, Department, ReceptPerson, ReceptStaff
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
        recept.stream = stream
        recept.date = datetime.strptime(recept.date, '%Y-%m-%d')
        recept.save()
        for person in personList:
            person.recept = recept
            person.save()
        for staff in staffList:
            staff.recept = recept
            staff.save()
        self.fields['applyDate'].widget.attrs['readonly'] = True
        self.fields['workId'].widget.attrs['readonly'] = True
        self.fields['name'].widget.attrs['readonly'] = True
        return render(request, 'FiProcess/approvalRecept.html',
            {'form': self, 'created': True, 'recept': recept, 'stream': stream, 'department': stream.department.name,
                'personList': personList, 'staffList': staffList})

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
        form.fields['applyDate'].widget.attrs['readonly'] = True
        form.fields['workId'].widget.attrs['readonly'] = True
        form.fields['name'].widget.attrs['readonly'] = True
        return render(request, 'FiProcess/approvalRecept.html',
            {'form': form, 'created': True, 'recept': recept, 'stream': stream, 'department': stream.department.name,
                'personList': personList, 'staffList': staffList})

    def submitPost(self, request):
        messages.add_message(request, messages.SUCCESS, u'提交成功')
        return HttpResponseRedirect(reverse('index', args={''}))
