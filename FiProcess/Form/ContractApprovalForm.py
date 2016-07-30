# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from datetime import datetime

from ..models import Staff
import IndexForm


class ContractApprovalForm(forms.Form):
    applyDate = forms.CharField(
        label=u'申请日期',
    )
    department = forms.CharField(
        label=u'经办单位',
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
            initial={'applyDate': datetime.now().strftime('%Y-%m-%d'), 'department': user.department.name,
                'name': user.name}
        )
        return render(request, 'FiProcess/approvalContract.html', {'form': form})
