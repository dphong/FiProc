# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django.forms import ModelForm
from django.utils import timezone
from datetime import datetime
from copy import deepcopy

from ..models import Stuff, FiStream


class CommonStreamForm(ModelForm):

    class Meta:
        model = FiStream
        fields = ['applyDate', 'supportDept', 'projectName', 'streamDiscript']
        labels = {
            'applyDate': u'报销日期',
            'supportDept': u'经费来源所属部门',
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

    class IcbcPay:

        def __init__(self):
            self.name = ''
            self.date = ''
            self.amount = 0.0
            self.actualAmount = 0.0
            self.icbcCard = ''
            self.payType = 0

    icbcPayList = []

    class CashPay:

        def __init__(self):
            self.name = ''
            self.amount = 0.0
            self.ccbCard = ''
            self.bankName = ''
            self.payType = 0

    ccbCashList = []
    companyAccountList = []

    def getStuffFromRequest(self, request):
        username = request.session['username']
        stuff = Stuff.objects.filter(username__exact=username)
        if not stuff or stuff.count() > 1:
            return None
        stuff = Stuff.objects.get(username__exact=username)
        return stuff

    def showCommonStream(self, request):
        stuff = self.getStuffFromRequest(request)
        if not stuff:
            return self.logout(request, '用户信息异常，请保存本条错误信息，并联系管理员')
        form = CommonStreamForm(
            initial={'department': stuff.department.name,
                'name': stuff.name, 'workId': stuff.workId, 'applyDate': timezone.now(),
                'projectLeaderWorkId': stuff.workId, 'projectLeaderName': stuff.name}
        )
        return render_to_response('FiProcess/commonStream.html', RequestContext(request, {'form': form}))

    def commonStreamPost(self, request):
        form = CommonStreamForm(request.POST)
        if not form.is_valid():
            return render_to_response('FiProcess/commonStream.html', RequestContext(request, {'form': form}))
        i = 1
        while ('icbc_cardHolderName' + str(i)) in request.POST:
            record = self.IcbcPay()
            record.name = request.POST['icbc_cardHolderName' + str(i)]
            record.date = request.POST['icbc_date' + str(i)]
            record.amount = request.POST['icbc_amount' + str(i)]
            record.actualAmount = request.POST['icbc_actualAmount' + str(i)]
            record.icbcCard = request.POST['icbc_account' + str(i)]
            record.payType = request.POST['icbc_spendType' + str(i)]
            try:
                datetime.strptime(request.POST['icbc_date' + str(i)], '%Y-%m-%d')
            except:
                icbcList = []
                icbcList = deepcopy(self.icbcPayList)
                icbcList.append(record)
                return render_to_response('FiProcess/commonStream.html',
                    RequestContext(request, {'form': form, 'list': icbcList,
                        'errorMsg': u'请正确填写第' + str(i) + u'条公务卡刷卡日期'}))
            try:
                record.amount = float(request.POST['icbc_amount' + str(i)])
            except:
                icbcList = []
                icbcList = deepcopy(self.icbcPayList)
                icbcList.append(record)
                return render_to_response('FiProcess/commonStream.html',
                    RequestContext(request, {'form': form, 'list': icbcList,
                        'errorMsg': u'请正确填写第' + str(i) + u'条公务卡刷卡金额'}))
            try:
                record.actualAmount = float(request.POST['icbc_actualAmount' + str(i)])
            except:
                icbcList = []
                icbcList = deepcopy(self.icbcPayList)
                icbcList.append(record)
                return render_to_response('FiProcess/commonStream.html',
                    RequestContext(request, {'form': form, 'list': icbcList,
                        'errorMsg': u'请正确填写第' + str(i) + u'条公务卡实报金额'}))
            try:
                Stuff.objects.get(name__exact=record.name, icbcCard__exact=record.icbcCard)
            except:
                icbcList = []
                icbcList = deepcopy(self.icbcPayList)
                icbcList.append(record)
                return render_to_response('FiProcess/commonStream.html',
                    RequestContext(request, {'form': form, 'list': icbcList,
                        'warningMsg': u'第' + str(i) + u'条公务卡未在系统中注册，请核对无误'}))
        return render_to_response('FiProcess/commonStream.html', RequestContext(request, {'form': form}))
