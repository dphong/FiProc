# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.forms import ModelForm
from datetime import datetime

from ..models import FiStream, TravelRecord, Department, Staff, SpendProof, Traveler, TravelRoute, IcbcCardRecord
import IndexForm


class TravelStreamForm(ModelForm):
    class Meta:
        model = FiStream
        fields = ['applyDate', 'projectName', 'descript']
        labels = {
            'applyDate': u'报销日期',
            'projectName': u'经费来源项目名称',
            'descript': u'经费使用目的',
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
        form = TravelStreamForm(
            initial={'descript': stream.descript, 'department': stream.applicante.department.name, 'projectName': stream.projectName,
                'name': stream.applicante.name, 'workId': stream.applicante.workId, 'applyDate': datetime.today().strftime('%Y-%m-%d'),
                'projectLeaderWorkId': stream.applicante.workId, 'projectLeaderName': stream.applicante.name,
                'cashReceiverId': stream.applicante.workId, 'cashReceiver': stream.applicante.name,
                'cardNum': stream.applicante.ccbCard}
        )
        try:
            record = TravelRecord.objects.get(fiStream__id=stream.id)
        except:
            messages.add_message(request, messages.ERROR, '查找报销单失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        if stream.stage == 'approved':
            record.leaveDate = record.leaveDate.strftime('%Y-%m-%d')
            record.returnDate = record.returnDate.strftime('%Y-%m-%d')
            return render(request, 'FiProcess/travelStream.html',
                {'form': form, 'record': record, 'fundDepartment': stream.department})
        travelerList = Traveler.objects.filter(record__id=record.id)
        routeList = TravelRoute.objects.filter(record__id=record.id)
        for route in routeList:
            route.date = route.date.strftime('%Y-%m-%d')
        cashList = SpendProof.objects.filter(fiStream__id=stream.id).exclude(proofDescript='icbc')
        icbcList = IcbcCardRecord.objects.filter(spendProof__fiStream__id=stream.id)
        icbcPayList = []
        for record in icbcList:
            icbc = self.IcbcPay()
            icbc.date = record.date.strftime('%Y-%m-%d')
            icbc.name = record.staff.name
            icbc.amount = record.spendProof.spendAmount
            icbc.actualAmount = icbc.amount - record.cantApplyAmount
            icbc.payType = record.spendProof.spendType
            icbc.icbcCard = record.staff.icbcCard
            icbcPayList.append(icbc)
        return render(request, 'FiProcess/travelStream.html',
            {'form': form, 'fundDepartment': stream.department, 'ccbList': cashList, 'travelerList': travelerList,
             'routeList': routeList, 'list': icbcPayList})

    def postNew(self, request):
        staff = IndexForm.getStaffFromRequest(request)
        if not staff:
            return IndexForm.logout(request, '当前用户登陆异常')
        form = TravelStreamForm(
            initial={'department': staff.department.name,
                'name': staff.name, 'workId': staff.workId, 'applyDate': datetime.today().strftime('%Y-%m-%d'),
                'projectLeaderWorkId': staff.workId, 'projectLeaderName': staff.name,
                'cashReceiverId': staff.workId, 'cashReceiver': staff.name,
                'cardNum': staff.ccbCard}
        )
        return render(request, 'FiProcess/travelStream.html', {'form': form, 'departmentList': Department.objects.filter()})

    class IcbcPay:
        def __init__(self):
            self.name = ''
            self.date = ''
            self.amount = 0.0
            self.actualAmount = 0.0
            self.icbcCard = ''
            self.payType = 0
            self.staff = None

    def post(self, request):
        record = None
        stream = None
        departmentList = None
        if 'streamId' in request.session:
            try:
                stream = FiStream.objects.get(id=request.session['streamId'])
                record = TravelRecord.objects.get(fiStream__id=stream.id)
                # clear old for modify operate
                queryList = Traveler.objects.filter(record__id=record.id)
                queryList.delete()
                queryList = TravelRoute.objects.filter(record__id=record.id)
                queryList.delete()
                queryList = IcbcCardRecord.objects.filter(spendProof__fiStream__id=stream.id)
                queryList.delete()
                queryList = SpendProof.objects.filter(fiStream__id=stream.id)
                queryList.delete()
            except:
                messages.add_message(request, messages.ERROR, u'操作失败')
                return HttpResponseRedirect(reverse('index', args={''}))
        else:
            stream = FiStream()
            staff = IndexForm.getStaffFromRequest(request)
            if not staff:
                return IndexForm.logout(request, '当前用户登陆异常')
            stream.applicante = staff
            try:
                dept = Department.objects.get(id=request.POST['supportDept'])
            except:
                messages.add_message(request, messages.ERROR, u'操作失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            stream.department = dept
            stream.stage = 'create'
            stream.streamType = 'travel'
            record = TravelRecord()
            departmentList = Department.objects.filter()
        errorMsg = []
        stream.applyDate = request.POST['applyDate']
        try:
            datetime.strptime(stream.applyDate, '%Y-%m-%d')
        except:
            errorMsg.append('报销日期格式错误')
        stream.projectName = request.POST['projectName']
        stream.descript = request.POST['descript']
        plWorkId = request.POST['projectLeaderWorkId']
        plName = request.POST['projectLeaderName']
        try:
            pl = Staff.objects.get(workId=plWorkId)
            if pl.name != plName:
                errorMsg.append('项目负责人姓名、工号与系统信息不符')
            stream.projectLeader = pl
        except:
            errorMsg.append('项目负责人工号不存在')
        cashId = request.POST['cashReceiverId']
        cashName = request.POST['cashReceiver']
        cashNum = request.POST['cardNum']
        casher = None
        try:
            casher = Staff.objects.get(workId=cashId)
            if casher.name != cashName:
                errorMsg.append('现金收款人姓名、工号与系统信息不符')
            if casher.ccbCard != cashNum:
                errorMsg.append('现金收款人建行工资卡号与系统信息不符')
        except:
            errorMsg.append('现金收款人工号不存在')
        i = 1
        cashList = []
        while ('ccb_amount' + str(i)) in request.POST:
            cash = SpendProof()
            cash.spendAmount = request.POST['ccb_amount' + str(i)]
            try:
                float(cash.spendAmount)
            except:
                errorMsg.append('第' + str(i) + '条现金支付记录金额错误')
            cash.spendType = request.POST['ccb_spendType' + str(i)]
            if casher:
                cash.proofDescript = str(casher.id)
            else:
                cash.proofDescript = ''
            cashList.append(cash)
            i = i + 1
        i = 1
        travelerList = []
        while ('name_traveler' + str(i)) in request.POST:
            traveler = Traveler()
            traveler.name = request.POST['name_traveler' + str(i)]
            traveler.duty = request.POST['duty_traveler' + str(i)]
            travelerList.append(traveler)
            i = i + 1
        i = 1
        routeList = []
        while ('travelRoute_date' + str(i)) in request.POST:
            route = TravelRoute()
            route.date = request.POST['travelRoute_date' + str(i)]
            try:
                datetime.strptime(route.date, '%Y-%m-%d')
            except:
                errorMsg.append('第' + str(i) + '条城市间交通记录日期错误')
            route.start = request.POST['start_position' + str(i)]
            route.end = request.POST['end_position' + str(i)]
            route.amount = request.POST['travelRoute_amount' + str(i)]
            try:
                float(route.amount)
            except:
                errorMsg.append('第' + str(i) + '条城市交通记录金额错误')
            routeList.append(route)
            i = i + 1
        i = 1
        icbcList = []
        while ('icbc_cardHolderName' + str(i)) in request.POST:
            icbc = self.IcbcPay()
            icbc.name = request.POST['icbc_cardHolderName' + str(i)]
            icbc.icbcCard = request.POST['icbc_account' + str(i)]
            try:
                staff = Staff.objects.get(icbcCard=icbc.icbcCard)
                if staff.name != icbc.name:
                    raise Exception('')
                icbc.staff = staff
            except:
                errorMsg.append('第' + str(i) + '条公务卡刷卡记录卡号，姓名错误')
            icbc.date = request.POST['icbc_date' + str(i)]
            try:
                datetime.strptime(icbc.date, '%Y-%m-%d')
            except:
                errorMsg.append('第' + str(i) + '条公务卡刷卡日期错误')
            icbc.amount = request.POST['icbc_amount' + str(i)]
            try:
                float(icbc.amount)
            except:
                errorMsg.append('\n第' + str(i) + '条公务卡刷卡金额错误')
            icbc.actualAmount = request.POST['icbc_actualAmount' + str(i)]
            try:
                float(icbc.actualAmount)
            except:
                errorMsg.append('\n第' + str(i) + '条公务卡刷卡记录实付金额错误')
            icbc.payType = request.POST['icbc_spendType' + str(i)]
            icbcList.append(icbc)
            i = i + 1
        if not self.is_valid() or len(errorMsg) > 0:
            form = TravelStreamForm(
                initial={'department': stream.applicante.department.name, 'projectName': stream.projectName, 'descript': stream.descript,
                    'name': stream.applicante.name, 'workId': stream.applicante.workId, 'applyDate': stream.applyDate, 'cashReceiverId': cashId,
                    'cashReceiver': cashName, 'cardNum': cashNum, 'projectLeaderWorkId': plWorkId, 'projectLeaderName': plName}
            )
            if (len(errorMsg) == 0):
                errorMsg = None
            return render(request, 'FiProcess/travelStream.html',
                {'form': form, 'departmentList': departmentList, 'fundDepartment': stream.department, 'ccbList': cashList, 'travelerList': travelerList,
                 'routeList': routeList, 'list': icbcList, 'errorMsg': errorMsg})
        stream.applyDate = self.cleaned_data['applyDate']
        stream.projectName = self.cleaned_data['projectName']
        stream.descript = self.cleaned_data['descript']
        stream.stage = 'create'
        stream.save()
        for spendProof in cashList:
            spendProof.fiStream = stream
            spendProof.save()
        if stream.stage == 'create':
            record.fiStream = stream
            record.duty = ''
            record.companionCnt = len(travelerList)
            if len(routeList) > 0:
                record.leaveDate = datetime.strptime(routeList[0].date, '%Y-%m-%d')
                record.destination = routeList[0].end
                record.startPosition = routeList[0].start
            else:
                record.leaveDate = datetime.now()
                record.returnDate = datetime.now()
                record.destination = ''
                record.startPosition = ''
            if len(routeList) > 1:
                record.returnDate = datetime.strptime(routeList[1].date, '%Y-%m-%d')
            else:
                record.returnDate = datetime.now()
            record.travelGrant = 0.0
            record.foodGrant = 0.0
            record.reason = stream.descript
            record.travelType = ''
            record.travelDescript = ''
            record.save()
        for traveler in travelerList:
            traveler.record = record
            traveler.save()
        for route in routeList:
            route.record = record
            route.save()
        for icbc in icbcList:
            proof = SpendProof()
            proof.fiStream = stream
            proof.spendType = icbc.payType
            proof.spendAmount = float(icbc.amount)
            proof.proofDescript = 'icbc'
            proof.save()
            icbcRecord = IcbcCardRecord()
            icbcRecord.spendProof = proof
            icbcRecord.staff = icbc.staff
            icbcRecord.date = datetime.strptime(icbc.date, '%Y-%m-%d')
            icbcRecord.cantApplyAmount = float(icbc.amount) - float(icbc.actualAmount)
            icbcRecord.cantApplyReason = ''
            icbcRecord.save()
        request.session['streamId'] = stream.id
        return HttpResponseRedirect(reverse('index', args={'streamDetail'}))
