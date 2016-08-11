# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from django.db.models import Q

import FormPublic
from ..models import Staff, SignRecord, FiStream


class HistoryForm(forms.Form):
    def sortOrder(self, stream):
        return stream.cwcSubmitDate

    def sortSignOrder(self, sign):
        return sign.stream.cwcSubmitDate

    typeDic = {'common': u'普通', 'travel': u'差旅', 'labor': u'劳务',
        'travelApproval': u'差旅', 'receptApproval': u'公务接待', 'contractApproval': u'合同'}

    def getStreamRecord(self, stream):
        item = {}
        item['applicante'] = stream.applicante.name
        item['date'] = stream.applyDate.strftime('%Y-%m-%d')
        item['supportDept'] = stream.department.name
        item['projectName'] = stream.projectName
        item['streamType'] = self.typeDic[stream.streamType]
        item['id'] = stream.id
        return item

    def getMySign(self, request, staff):
        sign = SignRecord.objects.filter(Q(signer__id=staff.id), Q(signed=1))
        sortSign = sorted(sign, key=self.sortSignOrder)
        signList = []
        for item in sortSign:
            signList.append(self.getStreamRecord(item.stream))
        return JsonResponse(signList, safe=False)

    def getStream(self, request, staff, condition):
        stream = FiStream.objects.filter(Q(applicante__id=staff.id), Q(stage=condition)).order_by('applyDate')
        streamList = []
        for item in stream:
            streamList.append(self.getStreamRecord(item))
        return JsonResponse(streamList, safe=False)

    def get(self, request):
        try:
            staff = Staff.objects.get(username=request.session['username'])
        except:
            return FormPublic.logout(request, u'登录状态异常!')
        target = request.GET.get('target')
        if target == 'mySign':
            return self.getMySign(request, staff)
        elif target == 'successStream':
            return self.getStream(request, staff, 'cwcpaid')
        elif target == 'failStream':
            return self.getStream(request, staff, 'refused')
        elif target == 'successApproval':
            return self.getStream(request, staff, 'approved')
        request.session['history'] = target
        return render(request, 'FiProcess/history.html')

    def post(self, request):
        if 'returnIndex' in request.POST:
            del request.session['history']
            return HttpResponseRedirect(reverse('index', args={''}))
        for name, value in request.POST.iteritems():
            if name.startswith('checkStreamDetail'):
                try:
                    item = FiStream.objects.get(id=name[17:])
                except:
                    messages.add_message(request, messages.ERROR, u'操作失败')
                    return render(request, 'FiProcess/cwc.html', {'form': self})
                request.session['streamId'] = item.id
                return HttpResponseRedirect(reverse('index', args={'streamDetail'}))

        return render(request, 'FiProcess/history.html')
