# -*- coding: utf-8 -*-
from django.contrib import messages, auth
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from django.db.models import Q

from ..models import SignRecord, SchoolMaster, Staff, FiStaffCode


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


def getStreamStageInfo(stream, request):
    signList = SignRecord.objects.filter(stream__id=stream.id)
    if stream.stage == 'refused':
        refuseMsg = u"本报销单被拒绝审批"
        for item in signList:
            if item.refused:
                refuseMsg += u"，拒绝者：" + item.signer.name + u"，拒绝原因：" + item.descript
        return (signList, refuseMsg, False)
    elif stream.stage == 'finish':
        return (signList, u'报销审批流程结束', False)
    elif stream.stage == 'cwcSubmit':
        return (signList, u'报销单由财务处分配中, 项目流水号：' + stream.number, False)
    elif stream.stage == 'cwcChecking':
        return (signList, u'报销单由财务处"' + stream.cwcDealer.name
                + u'"处理中，项目流水号：' + stream.number
                + u' 预计处理时间：' + stream.cwcSubmitDate.strftime('%Y年%m月%d日 %H点').decode('utf-8') + u'左右',
                False)
    elif stream.stage == 'cwcpaid':
        return (signList, u'报销单已由财务付款，项目流水号：' + stream.number, False)
    elif (('project' in stream.stage)
            or ('department' in stream.stage)
            or ('school' in stream.stage)
            or (stream.stage == 'financial')):
        try:
            sign = signList.get(stage__exact=stream.stage)
        except:
            raise Exception('')
        firstSigner = False
        if sign.stage == 'department1':
            staff = getStaffFromRequest(request)
            if sign.signer.id == staff.id:
                firstSigner = True
        return (signList, u"报销单由 '" + sign.signer.name + u"' 审核中", firstSigner)
    return (signList, stream.stage, False)


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


def getSignedSigner(stream):
    signList = SignRecord.objects.filter(stream__id=stream.id)
    dept1 = None
    dept2 = None
    school1 = None
    school2 = None
    school3 = None
    for sign in signList:
        if sign.refused or not sign.signed:
            continue
        if sign.stage == 'department1':
            dept1 = sign
        if sign.stage == 'department2':
            dept2 = sign
        if sign.stage == 'school1':
            school1 = sign
        if sign.stage == 'school2':
            school2 = sign
        if sign.stage == 'school3':
            school3 = sign
    return (dept1, dept2, school1, school2, school3)


def numtoCny(num, append=True, space=' '):
    capNum = ['<font class="font6">零</font>',
            '<font class="font6">壹</font>',
            '<font class="font6">贰</font>',
            '<font class="font6">叁</font>',
            '<font class="font6">肆</font>',
            '<font class="font6">伍</font>',
            '<font class="font6">陆</font>',
            '<font class="font6">柒</font>',
            '<font class="font6">捌</font>',
            '<font class="font6">玖</font>']
    chara = ['<font class="font8">佰</font>',
            '<font class="font8">拾</font>',
            '<font class="font8">万</font>',
            '<font class="font8">仟</font>',
            '<font class="font8">佰</font>',
            '<font class="font8">拾</font>',
            '<font class="font8">元</font>',
            '<font class="font8">.</font>',
            '<font class="font8">角</font>',
            '<font class="font8">分</font>']
    snum = None
    if append:
        snum = str('%010.02f') % num
    else:
        snum = str(num)
    i = len(snum)
    if i > 10:
        return ''
    result = ''
    diff = len(chara) - i
    while i > 0:
        i -= 1
        if snum[i] == '.':
            continue
        result = space + capNum[int(snum[i])] + space + chara[i + diff] + result
    return result


def getFiCode(deptId, name):
    try:
        item = FiStaffCode.objects.get(Q(name=name, department__id=deptId))
        return item.code
    except:
        return u'不存在'


def streamStageChange(stream):
    if stream.stage == 'finish' or stream.stage == 'refuesd' or stream.stage == 'approved':
        return stream.stage
    querySet = SignRecord.objects.filter(stream__id=stream.id)
    stageDict = None
    finalStr = ''
    if ('receptApproval' == stream.streamType or 'contractApproval' == stream.streamType
            or ('travelApproval' == stream.streamType and 'approv' in stream.stage and 'approved' != stream.stage)):
        if len(querySet) == 0:
            return 'unapprove'
        stageDict = {'unapprove': 0, 'approvalDepartment': 1, 'approvalOffice': 2, 'approvalSchool': 3, 'approved': 4}
        finalStr = 'approved'
    elif (('travelApproval' == stream.streamType and ('approv' not in stream.stage or stream.stage == 'approved'))
            or 'labor' == stream.streamType
            or 'travel' == stream.streamType or 'common' == stream.streamType):
        if len(querySet) == 0:
            return 'create'
        stageDict = {'create': 0, 'project': 1, 'department1': 2, 'department2': 3, 'projectDepartment': 4,
                     'school1': 5, 'school2': 6, 'school3': 7, 'financial': 8, 'finish': 9}
        finalStr = 'finish'
    else:
        raise Exception(u'报销单类型错误')
    minUnsignedStage = ""
    for item in querySet:
        if not item.signed and (stageDict[item.stage] >= stageDict[stream.stage]):
            if len(minUnsignedStage) == 0 or stageDict[item.stage] < stageDict[minUnsignedStage]:
                minUnsignedStage = item.stage
    if len(minUnsignedStage) == 0:
        minUnsignedStage = finalStr
    return minUnsignedStage
