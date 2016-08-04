# -*- coding: utf-8 -*-
from django.contrib import messages, auth
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

from ..models import SignRecord, SchoolMaster, Staff, FiStream


def logout(request, message='已注销'):
    if request.user.is_authenticated():
        auth.logout(request)
    if request.session.get('username', ""):
        del request.session['username']
    messages.add_message(request, messages.SUCCESS, message)
    return HttpResponseRedirect(reverse('login'))


def getStaffFromRequest(request):
    try:
        staff = Staff.objects.get(username__exact=request.session['username'])
    except:
        return None
    return staff


def clearSession(request):
    if 'streamId' in request.session:
        del request.session['streamId']
    if 'TravelRecord' in request.session:
        del request.session['TravelRecord']
    if 'hireLaborId' in request.session:
        del request.session['hireLaborId']
    if 'staffLaborId' in request.session:
        del request.session['staffLaborId']


def getStreamStageInfo(stream):
    signList = SignRecord.objects.filter(stream__id=stream.id)
    if stream.stage == 'refused':
        refuseMsg = u"本报销单被拒绝审批"
        for item in signList:
            if item.refused:
                refuseMsg += u"，拒绝者：" + item.signer.name + u"，拒绝原因：" + item.descript
        return (signList, refuseMsg)
    elif stream.stage == 'finish':
        return (signList, u'报销审批流程结束')
    elif stream.stage == 'cwcSubmit':
        return (signList, u'报销单由财务处分配中, 项目流水号：' + stream.number)
    elif stream.stage == 'cwcChecking':
        return (signList, u'报销单由财务处"' + stream.cwcDealer.name + u'"处理中，项目流水号：' + stream.number)
    elif stream.stage == 'cwcpaid':
        return (signList, u'报销单已由财务付款，项目流水号：' + stream.number)
    elif (('project' in stream.stage)
            or ('department' in stream.stage)
            or ('school' in stream.stage)
            or (stream.stage == 'financial')):
        try:
            sign = signList.get(stage__exact=stream.stage)
        except:
            raise Exception('')
        return (signList, u"报销单由 '" + sign.signer.name + u"' 审核中")
    return (signList, stream.stage)


def getSigner(stream, amount, signList):
    sign1 = None
    sign11 = None
    sign12 = None
    schoolSign1 = None
    schoolSign2 = None
    schoolSign3 = None
    if amount <= 3000 and stream.department.secretary:
        sign1 = stream.department
    else:
        # (3000, 5000] region
        if stream.department.secretary:
            sign12 = stream.department
        else:
            sign11 = stream.department
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
    schoolSigner = None
    deptSigner = None
    unsigned = True
    for sign in signList:
        if sign.stage == 'school1':
            schoolSigner = sign
        if sign.stage == 'department1':
            deptSigner = sign
        if sign.signed:
            unsigned = False
    return (sign1, sign11, sign12, schoolSign1, schoolSign2, schoolSign3,
        schoolSigner, deptSigner, unsigned)
