# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from ..models import IcbcCardRecord, CompanyPayRecord, CashPay
import NewStreamForm


class CommonStreamDetail(forms.Form):
    department = forms.CharField(
        label=u'部门',
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ),
    )
    name = forms.CharField(
        label=u'报销人',
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ),
    )
    phone = forms.CharField(
        label=u'联系电话',
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ),
    )
    applyDate = forms.CharField(
        label=u'报销日期',
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ),
    )
    amount = forms.CharField(
        label=u'合计金额',
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ),
    )
    supportDept = forms.CharField(
        label=u'经费来源所属部门',
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ),
    )
    currentStage = forms.CharField()
    descript = forms.CharField(
        label=u'经费使用目的',
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ),
    )

    class TypeAmount:
        def __init__(self):
            self.type = ''
            self.amount = 0.0

    def getTypeAmountList(self, list):
        i = 1
        result = []
        for item in list:
            if item == 0:
                continue
            ta = self.TypeAmount()
            if i == 1:
                ta.type = '办公用品'
            elif i == 2:
                ta.type = '书报资料'
            elif i == 3:
                ta.type = '印刷费'
            elif i == 4:
                ta.type = '邮电费'
            elif i == 5:
                ta.type = '住宿费'
            elif i == 6:
                ta.type = '出国费'
            elif i == 7:
                ta.type = '维修维护'
            elif i == 8:
                ta.type = '医疗费'
            elif i == 9:
                ta.type = '会议费'
            elif i == 10:
                ta.type = '培训费'
            elif i == 11:
                ta.type = '招待费'
            elif i == 12:
                ta.type = '交通费'
            elif i == 13:
                ta.type = '专用材料'
            elif i == 14:
                ta.type = '设备购置'
            elif i == 15:
                ta.type = '其他'
            ta.amount = item
            result.append(ta)
            i += 1
        return result

    def get(self, request, stream):
        icbcQuery = IcbcCardRecord.objects.filter(spendProof__fiStream__id=stream.id)
        ccbQuery = CashPay.objects.filter(spendProof__fiStream__id=stream.id)
        comQuery = CompanyPayRecord.objects.filter(spendProof__fiStream__id=stream.id)
        amount = 0
        typeAmount = [0 for n in range(16)]
        for icbc in icbcQuery:
            amount = amount + icbc.spendProof.spendAmount
            typeAmount[int(icbc.spendProof.spendType)] += icbc.spendProof.spendAmount
            icbc.date = icbc.date.strftime('%Y-%m-%d')
            icbc.cantApplyAmount = icbc.spendProof.spendAmount - icbc.cantApplyAmount
        for ccb in ccbQuery:
            amount = amount + ccb.spendProof.spendAmount
            typeAmount[int(ccb.spendProof.spendType)] += ccb.spendProof.spendAmount
        for com in comQuery:
            amount = amount + com.spendProof.spendAmount
            typeAmount[int(com.spendProof.spendType)] += com.spendProof.spendAmount
        typeList = self.getTypeAmountList(typeAmount)
        try:
            signList, stageInfo = NewStreamForm.getStreamStageInfo(stream)
        except:
            messages.add_message(request, messages.ERROR, '审核状态异常')
            return HttpResponseRedirect(reverse('index', args={''}))
        form = CommonStreamDetail(
            initial={
                'department': stream.applicante.department.name,
                'name': stream.applicante.name,
                'phone': stream.applicante.phoneNumber,
                'applyDate': stream.applyDate.strftime('%Y-%m-%d'),
                'amount': str(amount),
                'supportDept': stream.department.name,
                'currentStage': stageInfo,
                'descript': stream.descript,
            }
        )
        if not stream.department.chief:
            return render(request, 'FiProcess/commonStreamDetail.html',
                {'form': form, 'typeList': typeList, 'icbcList': icbcQuery, 'ccbList': ccbQuery, 'comList': comQuery,
                    'signList': signList, 'signErrorMsg': u'所属部门负责人不存在!'})

        sign1, sign11, sign12, schoolSign1, schoolSign2, schoolSign3, schoolSigner, deptSigner, unsigned = NewStreamForm.getSigner(stream, amount, signList)
        return render(request, 'FiProcess/commonStreamDetail.html',
            {'form': form, 'typeList': typeList, 'icbcList': icbcQuery, 'ccbList': ccbQuery, 'comList': comQuery, 'signList': signList,
                'unsigned': unsigned, 'sign1': sign1, 'sign12': sign12, 'sign11': sign11, 'schoolSigner': schoolSigner, 'deptSigner': deptSigner,
                'schoolSign1': schoolSign1, 'schoolSign2': schoolSign2, 'schoolSign3': schoolSign3})
