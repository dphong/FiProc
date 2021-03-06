# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages
from django.db.models import Q
from datetime import datetime
from django.contrib.auth.hashers import check_password

from CommonStreamForm import CommonStreamForm
from CommonStreamDetail import CommonStreamDetail
from TravelStreamForm import TravelStreamForm
from TravelStreamDetail import TravelStreamDetail
from LaborStreamForm import LaborStreamForm
import FormPublic

from ..models import FiStream, SignRecord, SchoolMaster


class NewStreamForm(forms.Form):
    def get(self, request):
        if 'streamId' not in request.session:
            return render(request, 'FiProcess/newStream.html')
        try:
            stream = FiStream.objects.get(id=request.session['streamId'])
        except:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        if stream.streamType == 'common':
            form = CommonStreamForm(request.GET)
            return form.modify(request, stream)
        if stream.streamType == 'travelApproval':
            form = TravelStreamForm(request.GET)
            return form.get(request, stream)
        return render(request, 'FiProcess/newStream.html')

    def newFiStreamType(self, request):
        streamType = request.POST['newStreamType']
        if streamType == 'common':
            form = CommonStreamForm(request.POST)
            return form.get(request)
        if streamType == 'travel':
            return render(request, 'FiProcess/travelWarning.html')
        if streamType == 'labor':
            form = LaborStreamForm(request.POST)
            return form.get(request)
        return render(request, 'FiProcess/newStream.html')

    def laborPost(self, request):
        for name, value in request.POST.iteritems():
            if name.startswith('delStaffLaborPay'):
                form = LaborStreamForm(request.POST)
                return form.delStaffLaborPay(request, int(name[16:]))
            if name.startswith('modifyStaffLaborPay'):
                form = LaborStreamForm(request.POST)
                return form.modifyStaffLaborPay(request, int(name[19:]))
            if name.startswith('delHireLaborPay'):
                form = LaborStreamForm(request.POST)
                return form.delHireLaborPay(request, int(name[15:]))
            if name.startswith('modifyHireLaborPay'):
                form = LaborStreamForm(request.POST)
                return form.modifyHireLaborPay(request, int(name[18:]))
        return None

    def post(self, request):
        if "newStreamType" in request.POST:
            return self.newFiStreamType(request)
        if 'createNewTravelStream' in request.POST:
            form = TravelStreamForm(request.POST)
            return form.postNew(request)
        if 'travelStreamForm' in request.POST:
            form = TravelStreamForm(request.POST)
            return form.post(request)
        if "commonStreamForm" in request.POST:
            form = CommonStreamForm(request.POST)
            return form.post(request)
        if "addLaborRow" in request.POST:
            form = LaborStreamForm(request.POST)
            return form.postAddRow(request)
        if "modifyLaborRow" in request.POST:
            form = LaborStreamForm(request.POST)
            return form.postModifyRow(request)
        if "laborStreamForm" in request.POST:
            return self.postDetail(request)
        if "createStream" in request.POST:
            return self.postDetail(request)
        response = self.laborPost(request)
        if response:
            return response
        return render(request, 'FiProcess/newStream.html')

    def getDetail(self, request):
        if 'streamId' not in request.session:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        try:
            stream = FiStream.objects.get(id=request.session['streamId'])
        except:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        if stream.streamType == 'common':
            detail = CommonStreamDetail(request.GET)
            return detail.get(request, stream)
        if stream.streamType == 'travel':
            detail = TravelStreamDetail(request.GET)
            return detail.get(request, stream)
        if stream.streamType == 'labor':
            detail = LaborStreamForm(request.GET)
            return detail.getDetail(request, stream)
        if (stream.streamType == 'travelApproval'or stream.streamType == 'receptApproval'or stream.streamType == 'contractApproval'):
            if 'approv' in stream.stage:
                return HttpResponseRedirect(reverse('index', args={'approvalDetail'}))
            detail = TravelStreamDetail(request.GET)
            return detail.get(request, stream)
        return HttpResponseRedirect(reverse('index', args={''}))

    def postDetail(self, request):
        if 'streamId' not in request.session:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        if 'modifyStream' in request.POST:
            return HttpResponseRedirect(reverse('index', args={'newstream'}))
        streamId = request.session['streamId']
        try:
            stream = FiStream.objects.get(id=streamId)
        except:
            messages.add_message(request, messages.ERROR, u'查找报销单失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        if 'createStream' in request.POST:
            return self.signPost(request, stream)
        if "addLaborRow" in request.POST:
            form = LaborStreamForm(request.POST)
            return form.postAddRow(request)
        if "modifyLaborRow" in request.POST:
            form = LaborStreamForm(request.POST)
            return form.postModifyRow(request)
        if "laborStreamForm" in request.POST:
            form = LaborStreamForm(request.POST)
            return form.post(request, stream)
        if "modifyLaborStream" in request.POST:
            form = LaborStreamForm(request.POST)
            return form.modifyCreatedForm(request, stream)
        if "signOkConfirm" in request.POST:
            staff = FormPublic.getStaffFromRequest(request)
            if not staff:
                return FormPublic.logout(request, '用户信息异常，或未登录系统')
            if not check_password(request.POST['signOkPassword'], staff.password):
                messages.add_message(request, messages.ERROR, u'密码错误')
                return HttpResponseRedirect(reverse('index', args={''}))
            try:
                item = SignRecord.objects.get(Q(stream__id=stream.id), Q(stage='department1'), Q(signer__id=staff.id))
            except:
                messages.add_message(request, messages.ERROR, u'操作失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            item.signed = True
            item.descript = request.POST['signOkDescript']
            item.signedTime = datetime.now()
            item.save()
            try:
                item.stream.stage = FormPublic.streamStageChange(item.stream)
                item.stream.save()
            except Exception, e:
                messages.add_message(request, messages.ERROR, str(e))
                return HttpResponseRedirect(reverse('index', args={''}))
            messages.add_message(request, messages.SUCCESS, u'审核成功')
            return HttpResponseRedirect(reverse('index', args={''}))
        response = self.laborPost(request)
        if response:
            return response
        return HttpResponseRedirect(reverse('index', args={''}))

    def signPost(self, request, stream):
        sign1 = SignRecord()
        sign1.stream = stream
        if 'sign1' in request.POST:
            signer = request.POST['sign1']
        else:
            messages.add_message(request, messages.ERROR, '提交报销单失败, 未指定部门负责人')
            return HttpResponseRedirect(reverse('index', args={''}))
        if stream.department.chief and str(stream.department.chief.id) == signer:
            sign1.signer = stream.department.chief
        elif stream.department.secretary and str(stream.department.secretary.id) == signer:
            sign1.signer = stream.department.secretary
        elif stream.department.chief and stream.department.chief.name == signer:
            sign1.signer = stream.department.chief
        else:
            messages.add_message(request, messages.ERROR, '提交报销单失败, 查找部门负责人失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        sign1.stage = 'department1'
        sign2 = None
        schoolSign1 = None
        schoolSign2 = None
        schoolSign3 = None
        if 'sign2' in request.POST:
            sign2 = SignRecord()
            sign2.stream = stream
            signer = request.POST['sign2']
            if stream.department.secretary and stream.department.secretary.name == signer:
                sign2.signer = stream.department.secretary
            else:
                messages.add_message(request, messages.ERROR, '提交报销单失败, 查找部门书记失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            sign2.stage = 'department2'
        if 'schoolSign1' in request.POST:
            schoolSign1 = SignRecord()
            schoolSign1.stream = stream
            signer = request.POST['schoolSign1']
            try:
                schoolSign1.signer = SchoolMaster.objects.get(Q(staff__id=signer), Q(duty='school1')).staff
            except:
                messages.add_message(request, messages.ERROR, '提交报销单失败, 查找分管校长信息失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            schoolSign1.stage = 'school1'
        if 'schoolSign2' in request.POST:
            schoolSign2 = SignRecord()
            schoolSign2.stream = stream
            signer = request.POST['schoolSign2']
            try:
                schoolSign2.signer = SchoolMaster.objects.get(Q(staff__name__exact=signer), Q(duty='school2')).staff
            except:
                messages.add_message(request, messages.ERROR, '提交报销单失败, 查找主管财务校长信息失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            schoolSign2.stage = 'school2'
        if 'schoolSign3' in request.POST:
            schoolSign3 = SignRecord()
            schoolSign3.stream = stream
            signer = request.POST['schoolSign3']
            try:
                schoolSign3.signer = SchoolMaster.objects.get(Q(staff__id=signer), Q(duty='school3')).staff
            except:
                messages.add_message(request, messages.ERROR, '提交报销单失败, 查找校长信息失败')
                return HttpResponseRedirect(reverse('index', args={''}))
            schoolSign3.stage = 'school3'
        messages.add_message(request, messages.SUCCESS, '提交报销单成功')
        sign1.save()
        stream.stage = 'department1'
        stream.save()
        if sign2:
            sign2.save()
        if schoolSign1:
            schoolSign1.save()
        if schoolSign2:
            schoolSign2.save()
        if schoolSign3:
            schoolSign3.save()
        return HttpResponseRedirect(reverse('index', args={''}))
