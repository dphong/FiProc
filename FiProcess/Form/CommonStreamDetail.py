# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from ..models import IcbcCardRecord, CompanyPayRecord
from ..models import CashPay, SchoolMaster, SignRecord


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
        form = CommonStreamDetail(
            initial={
                'department': stream.applicante.department.name,
                'name': stream.applicante.name,
                'phone': stream.applicante.phoneNumber,
                'applyDate': stream.applyDate.strftime('%Y-%m-%d'),
                'amount': str(amount),
                'supportDept': stream.supportDept.name,
                'currentStage': stream.currentStage,
                'descript': stream.streamDescript,
            }
        )
        if not stream.supportDept.chief:
            return render(request, 'FiProcess/commonStreamDetail.html',
                {'form': form, 'typeList': typeList, 'icbcList': icbcQuery, 'ccbList': ccbQuery, 'comList': comQuery,
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
        return render(request, 'FiProcess/commonStreamDetail.html',
            {'form': form, 'typeList': typeList, 'icbcList': icbcQuery, 'ccbList': ccbQuery, 'comList': comQuery, 'signList': signList,
                'unsigned': unsigned, 'sign1': sign1, 'sign12': sign12, 'sign11': sign11, 'schoolSigner': school1Id, 'signId': signId,
                'schoolSign1': schoolSign1, 'schoolSign2': schoolSign2, 'schoolSign3': schoolSign3})

    def post(self, request, stream):
        sign1 = SignRecord()
        sign1.stream = stream
        if 'sign1' in request.POST:
            signer = request.POST['sign1']
        else:
            messages.add_message(request, messages.ERROR, '提交报销单失败, 未指定部门负责人')
            return HttpResponseRedirect(reverse('index', args={''}))
        if stream.supportDept.chief and str(stream.supportDept.chief.id) == signer:
            sign1.signer = stream.supportDept.chief
        elif stream.supportDept.secretary and str(stream.supportDept.secretary.id) == signer:
            sign1.signer = stream.supportDept.secretary
        else:
            messages.add_message(request, messages.ERROR, '提交报销单失败, 查找部门负责人失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        sign1.stage = 'department1'
        sign1.save()
        stream.currentStage = 'department1'
        stream.save()
        if 'sign2' in request.POST:
            sign2 = SignRecord()
            sign2.stream = stream
            signer = request.POST['sign2']
            if stream.supportDept.secretary and stream.supportDept.secretary.name == signer:
                sign2.signer = stream.supportDept.secretary
            else:
                messages.add_message(request, messages.ERROR, '提交报销单失败, 查找部门书记失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            sign2.stage = 'department2'
            sign2.save()
        if 'schoolSign1' in request.POST:
            schoolSign1 = SignRecord()
            schoolSign1.stream = stream
            signer = request.POST['schoolSign1']
            try:
                schoolSign1.signer = SchoolMaster.objects.get(staff__username=signer).staff
            except:
                messages.add_message(request, messages.ERROR, '提交报销单失败, 查找分管校长信息失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            schoolSign1.stage = 'school1'
            schoolSign1.save()
        if 'schoolSign2' in request.POST:
            schoolSign2 = SignRecord()
            schoolSign2.stream = stream
            signer = request.POST['schoolSign2']
            try:
                schoolSign2.signer = SchoolMaster.objects.get(staff__name__exact=signer).staff
            except:
                messages.add_message(request, messages.ERROR, '提交报销单失败, 查找主管财务校长信息失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            schoolSign2.stage = 'school2'
            schoolSign2.save()
        if 'schoolSign3' in request.POST:
            schoolSign3 = SignRecord()
            schoolSign3.stream = stream
            signer = request.POST['schoolSign3']
            try:
                schoolSign3.signer = SchoolMaster.objects.get(staff__name__exact=signer).staff
            except:
                messages.add_message(request, messages.ERROR, '提交报销单失败, 查找校长信息失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            schoolSign3.stage = 'school3'
            schoolSign3.save()
        messages.add_message(request, messages.SUCCESS, '提交报销单成功')
        return HttpResponseRedirect(reverse('index', args={''}))
