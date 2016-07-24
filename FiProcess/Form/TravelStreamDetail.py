# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from ..models import SpendProof, IcbcCardRecord, TravelRecord, Traveler, TravelRoute
from ..models import SchoolMaster, SignRecord


class TravelStreamDetail(forms.Form):
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
    projectName = forms.CharField(
        label=u'项目名称',
        widget=forms.TextInput(
            attrs={'readonly': 'readonly'}
        ),
    )

    class TypeAmount:
        def __init__(self):
            self.type = ''
            self.amount = 0.0

    def getTypeStr(self, i):
        if i == 1:
            return '城市间交通费'
        elif i == 2:
            return '住宿费'
        elif i == 3:
            return '会务费'
        elif i == 4:
            return '市内交通费'
        return '其他'

    def getTypeAmountList(self, list):
        i = 1
        result = []
        for item in list:
            if item == 0:
                continue
            ta = self.TypeAmount()
            ta.type = self.getTypeStr(i)
            ta.amount = item
            result.append(ta)
            i += 1
        return result

    def get(self, request, stream):
        try:
            record = TravelRecord.objects.get(fiStream__id=stream.id)
        except:
            messages.add_message(request, messages.ERROR, '查找差旅报销单信息失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        cashList = SpendProof.objects.filter(fiStream__id=stream.id).exclude(proofDescript='icbc')
        travelerList = Traveler.objects.filter(record__id=record.id)
        travelRouteList = TravelRoute.objects.filter(record__id=record.id)
        icbcList = IcbcCardRecord.objects.filter(spendProof__fiStream__id=stream.id)
        amount = 0
        typeAmount = [0 for n in range(6)]
        for cash in cashList:
            amount += cash.spendAmount
            typeAmount[int(cash.spendType)] += cash.spendAmount
            cash.spendType = self.getTypeStr(int(cash.spendType))
        for icbc in icbcList:
            actualAmount = icbc.spendProof.spendAmount - icbc.cantApplyAmount
            amount += actualAmount
            typeAmount[int(icbc.spendProof.spendType)] += actualAmount
            icbc.date = icbc.date.strftime('%Y-%m-%d')
            icbc.cantApplyAmount = actualAmount
        for route in travelRouteList:
            route.date = route.date.strftime('%Y-%m-%d')
        typeList = self.getTypeAmountList(typeAmount)
        signList = SignRecord.objects.filter(stream__id=stream.id)
        if stream.currentStage == 'refused':
            refuseMsg = u"本报销单被拒绝审批"
            for item in signList:
                if item.refused:
                    refuseMsg += u"，拒绝者：" + item.signer.name + u"，拒绝原因：" + item.descript
            stream.currentStage = refuseMsg
        elif stream.currentStage == 'finish':
            stream.currentStage = u'报销审批流程结束'
        elif stream.currentStage == 'cwcSubmit':
            stream.currentStage = u'报销单由财务处分配中'
        elif stream.currentStage == 'cwcChecking':
            stream.currentStage = u'报销单由财务处"' + stream.cwcDealer.name + u'"处理中'
        elif stream.currentStage == 'cwcpaid':
            stream.currentStage = u'报销单已由财务付款'
        elif stream.currentStage != 'create':
            try:
                sign = signList.get(stage__exact=stream.currentStage)
            except:
                messages.add_message(request, messages.ERROR, '审核状态异常')
                return HttpResponseRedirect(reverse('index', args={''}))
            stream.currentStage = u"报销单由 '" + sign.signer.name + u"' 审核中"
        form = TravelStreamDetail(
            initial={
                'department': stream.applicante.department.name,
                'name': stream.applicante.name,
                'phone': stream.applicante.phoneNumber,
                'applyDate': stream.applyDate.strftime('%Y-%m-%d'),
                'projectName': stream.projectName,
                'currentStage': stream.currentStage,
                'supportDept': stream.supportDept.name,
                'amount': str(amount),
            }
        )
        if not stream.supportDept.chief:
            return render(request, 'FiProcess/commonStreamDetail.html',
                {'form': form, 'stream': stream, 'typeList': typeList, 'icbcList': icbcList, 'cashList': cashList,
                    'signList': signList, 'signErrorMsg': u'所属部门负责人不存在!'})

        sign1 = None
        sign11 = None
        sign12 = None
        schoolSign1 = None
        schoolSign2 = None
        schoolSign3 = None
        if amount <= 3000 and stream.supportDept.secretary:
            sign1 = stream.supportDept
        else:
            # (3000, 5000] region
            if stream.supportDept.secretary:
                sign12 = stream.supportDept
            else:
                sign11 = stream.supportDept
            if amount > 5000:
                schoolSign1 = SchoolMaster.objects.filter(duty__exact='school1')
            if amount > 10000:
                try:
                    schoolSign2 = SchoolMaster.objects.get(duty__exact='school2')
                except:
                    schoolSign2 = None
            if amount > 200000:
                try:
                    schoolSign3 = SchoolMaster.objects.get(duty__exact='school3')
                except:
                    schoolSign3 = None
        school1Id = None
        signId = None
        unsigned = True
        for sign in signList:
            if sign.stage == 'school1':
                school1Id = sign.signer.id
            if sign.stage == 'department1':
                signId = sign.signer.id
            if sign.signed:
                unsigned = False
        return render(request, 'FiProcess/travelStreamDetail.html',
            {'form': form, 'typeList': typeList, 'cashList': cashList, 'travelerList': travelerList, 'travelRoute': travelRouteList,
                'icbcList': icbcList, 'signList': signList, 'stream': stream,
                'unsigned': unsigned, 'sign1': sign1, 'sign12': sign12, 'sign11': sign11, 'schoolSigner': school1Id, 'signId': signId,
                'schoolSign1': schoolSign1, 'schoolSign2': schoolSign2, 'schoolSign3': schoolSign3})
