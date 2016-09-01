# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from ..models import SpendProof, IcbcCardRecord, TravelRecord, Traveler, TravelRoute, Staff
import FormPublic


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

    def getTravelDetail(self, record):
        cashList = SpendProof.objects.filter(fiStream__id=record.fiStream.id).exclude(proofDescript='icbc')
        travelerList = Traveler.objects.filter(record__id=record.id)
        travelRouteList = TravelRoute.objects.filter(record__id=record.id)
        icbcList = IcbcCardRecord.objects.filter(spendProof__fiStream__id=record.fiStream.id)
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
            icbc.cantApplyAmount = actualAmount
        return (cashList, travelerList, travelRouteList, icbcList, amount, typeAmount)

    def get(self, request, stream):
        try:
            record = TravelRecord.objects.get(fiStream__id=stream.id)
        except:
            messages.add_message(request, messages.ERROR, '查找差旅报销单信息失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        cashList, travelerList, travelRouteList, icbcList, amount, typeAmount = self.getTravelDetail(record)
        typeList = self.getTypeAmountList(typeAmount)
        try:
            signList, stageInfo, firstSigner = FormPublic.getStreamStageInfo(stream, request)
        except:
            messages.add_message(request, messages.ERROR, '审核状态异常')
            return HttpResponseRedirect(reverse('index', args={''}))
        form = TravelStreamDetail(
            initial={
                'department': stream.applicante.department.name,
                'name': stream.applicante.name,
                'phone': stream.applicante.phoneNumber,
                'applyDate': stream.applyDate.strftime('%Y-%m-%d'),
                'projectName': stream.projectName,
                'currentStage': stageInfo,
                'supportDept': stream.department.name,
                'amount': str(amount),
            }
        )
        if not stream.department.chief:
            return render(request, 'FiProcess/travelStreamDetail.html',
                {'form': form, 'stream': stream, 'typeList': typeList, 'icbcList': icbcList, 'cashList': cashList,
                    'signList': signList, 'signErrorMsg': u'所属部门负责人不存在!'})

        sign1, sign11, sign12, schoolSign1, schoolSign2, schoolSign3, schoolSigner, schoolSigner3, deptSigner, unsigned = FormPublic.getSigner(stream, amount, signList)
        return render(request, 'FiProcess/travelStreamDetail.html',
            {'form': form, 'typeList': typeList, 'cashList': cashList, 'travelerList': travelerList, 'travelRoute': travelRouteList,
                'icbcList': icbcList, 'signList': signList, 'stream': stream,
                'unsigned': unsigned, 'sign1': sign1, 'sign12': sign12, 'sign11': sign11, 'schoolSigner': schoolSigner, 'schoolSigner3': schoolSigner3, 'deptSigner': deptSigner,
                'schoolSign1': schoolSign1, 'schoolSign2': schoolSign2, 'schoolSign3': schoolSign3, 'firstSigner': firstSigner})

    def printStream(self, request, stream):
        try:
            record = TravelRecord.objects.get(fiStream__id=stream.id)
        except:
            messages.add_message(request, messages.ERROR, '查找差旅报销单信息失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        cashList, rawTravelerList, rawTravelRouteList, rawIcbcList, amount, typeAmount = self.getTravelDetail(record)
        casher = stream.applicante
        if cashList and len(cashList[0].proofDescript) > 0:
            try:
                casher = Staff.objects.get(id=int(cashList[0].proofDescript))
            except:
                casher = stream.applicante
        dept1, dept2, school1, school2, school3 = FormPublic.getSignedSigner(stream)
        carPlate = None
        carDriver = None
        traveler = None
        travelerList = None
        icbc = None
        icbcList = None
        route = None
        routeList = None
        routeIdx = None
        if len(rawTravelerList) <= 4:
            traveler = rawTravelerList
        else:
            traveler = rawTravelerList[:3]
            travelerList = rawTravelerList[3:]
        if len(rawIcbcList) <= 5:
            icbc = rawIcbcList
        else:
            icbc = rawIcbcList[:4]
            icbcList = rawIcbcList[4:]
        if len(rawTravelRouteList) < 4:
            route = rawTravelRouteList
        else:
            route = rawTravelRouteList[3:]
            routeList = rawTravelRouteList[3:]
            routeIdx = 1
            if icbcList:
                routeIdx += 1
            if travelerList:
                routeIdx += 1
        if record.travelType == 'officialCar' or record.travelType == 'selfCar':
            carPlate = record.travelDescript[record.travelDescript.index(':') + 1:record.travelDescript.index(',')]
            carDriver = record.travelDescript[record.travelDescript.index(','):]
            carDriver = carDriver[carDriver.index(':') + 1:]
        casher.workId = FormPublic.getFiCode(casher.department.id, casher.name)
        return render(request, 'FiProcess/travelSheet.htm',
            {'stream': stream, 'casher': casher, 'record': record, 'carPlate': carPlate, 'carDriver': carDriver,
                'dept1': dept1, 'dept2': dept2, 'school1': school1, 'school2': school2, 'school3': school3,
                'typeAmount': typeAmount, 'traveler': traveler, 'travelerList': travelerList,
                'travelRoute': route, 'routeList': routeList, 'routeIdx': routeIdx,
                'icbc': icbc, 'icbcList': icbcList, 'amount': amount})
