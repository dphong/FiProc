# -*- coding: utf-8 -*-
from django import forms
from django.forms import ModelForm
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from datetime import datetime

from ..models import Staff, FiStream, Department
import IndexForm


class LaborStreamForm(ModelForm):
    class Meta:
        model = FiStream
        fields = ['applyDate', 'supportDept', 'projectName', 'streamDescript']
        labels = {
            'applyDate': u'报销日期',
            'supportDept': u'经费来源所属部门',
            'projectName': u'经费来源项目名称',
            'streamDescript': u'经费使用目的',
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
    projectLaborTime = forms.CharField(
        label=u'劳务发生时间'
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
