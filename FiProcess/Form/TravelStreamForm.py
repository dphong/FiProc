# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.forms import ModelForm
from datetime import datetime

from ..models import FiStream, TravelRecord, Department
import IndexForm


class TravelStreamForm(ModelForm):
    class Meta:
        model = FiStream
        fields = ['applyDate', 'projectName', 'streamDiscript']
        labels = {
            'applyDate': u'报销日期',
            'projectName': u'经费来源项目名称',
            'streamDiscript': u'经费使用目的',
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
    cashReceiverId = forms.CharField(
        label=u'现金收款人工(学)号'
    )
    cashReceiver = forms.CharField(
        label=u'收款人姓名'
    )
    cardNum = forms.CharField(
        label=u'建行工资卡号'
    )

    def get(self, request, stream):
        if stream.streamType == "travelApproval":
            stream.streamType = "travel"
            # stream.save()
            try:
                record = TravelRecord.objects.get(fiStream__id=stream.id)
            except:
                messages.add_message(request, messages.ERROR, '查找报销单失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            form = TravelStreamForm(
                initial={'streamDiscript': record.reason, 'department': stream.applicante.department.name,
                    'name': stream.applicante.name, 'workId': stream.applicante.workId, 'applyDate': datetime.today(),
                    'projectLeaderWorkId': stream.applicante.workId, 'projectLeaderName': stream.applicante.name,
                    'cashReceiverId': stream.applicante.workId, 'cashReceiver': stream.applicante.name,
                    'cardNum': stream.applicante.ccbCard}
            )
            record.leaveDate = datetime.strftime(record.leaveDate, '%Y-%m-%d')
            record.returnDate = datetime.strftime(record.returnDate, '%Y-%m-%d')
            return render(request, 'FiProcess/travelStream.html',
                {'form': form, 'record': record, 'fundDepartment': stream.supportDept})
        return self.newTravelForm(request, stream)

    def newTravelForm(self, request, stream):
        form = TravelStreamForm(
            initial={'department': stream.applicante.department.name,
                'name': stream.applicante.name, 'workId': stream.applicante.workId, 'applyDate': datetime.today(),
                'projectLeaderWorkId': stream.applicante.workId, 'projectLeaderName': stream.applicante.name,
                'cashReceiverId': stream.applicante.workId, 'cashReceiver': stream.applicante.name,
                'cardNum': stream.applicante.ccbCard}
        )
        return render(request, 'FiProcess/travelStream.html',
            {'form': form, 'departmentList': Department.objects.filter()})

    def postNew(self, request):
        staff = IndexForm.getStaffFromRequest(request)
        stream = FiStream()
        stream.applicante = staff
        return self.newTravelForm(request, stream)
