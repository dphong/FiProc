# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages
from datetime import datetime

from ..models import FiStream, Staff
import FormPublic


class CwcForm(forms.Form):
    def getStreamList(self, dealer=''):
        streamList = []
        if dealer == '':
            querySet = FiStream.objects.filter(stage='cwcSubmit')
        else:
            querySet = FiStream.objects.filter(stage='cwcChecking', cwcDealer__username=dealer)
        typeDic = {'common': u'普通', 'travel': u'差旅', 'labor': u'劳务', 'travelApproval': u'差旅'}
        querySet = sorted(querySet, key=self.sortOrder)
        for item in querySet:
            stream = {}
            stream['projectName'] = item.projectName
            stream['applicante'] = item.applicante.name
            stream['supportDept'] = item.department.name
            stream['streamType'] = typeDic[item.streamType]
            stream['time'] = item.cwcSubmitDate.strftime('%Y-%m-%d')
            if item.cwcSubmitDate.hour > 12:
                stream['time'] += u'下午'
            else:
                stream['time'] += u'上午'
            stream['id'] = item.id
            streamList.append(stream)
        return streamList

    def sortOrder(self, stream):
        return stream.cwcSubmitDate

    def get(self, request):
        try:
            staff = Staff.objects.get(username=request.session['username'])
        except:
            return FormPublic.logout(request, u'登录状态异常!')
        if staff.department.name != u'财务处':
            messages.add_message(request, messages.ERROR, u'操作异常')
            return HttpResponseRedirect(reverse('index', args={''}))
        request.session['office'] = 'cwc'
        if request.GET.get('target') == 'allStream':
            streamList = self.getStreamList()
            return JsonResponse(streamList, safe=False)
        elif request.GET.get('target') == 'myStream':
            streamList = self.getStreamList(request.session['username'])
            return JsonResponse(streamList, safe=False)
        return render(request, 'FiProcess/cwc.html', {'form': self})

    def post(self, request):
        if 'returnIndex' in request.POST:
            del request.session['office']
            return HttpResponseRedirect(reverse('index', args={''}))
        try:
            staff = Staff.objects.get(username=request.session['username'])
        except:
            return FormPublic.logout(request, u'登录状态异常!')
        if staff.department.name != u'财务处':
            messages.add_message(request, messages.ERROR, u'操作异常')
            return HttpResponseRedirect(reverse('index', args={''}))
        for name, value in request.POST.iteritems():
            if name.startswith('acceptStream'):
                try:
                    item = FiStream.objects.get(id=name[12:])
                except:
                    messages.add_message(request, messages.ERROR, u'处理失败')
                    return render(request, 'FiProcess/cwc.html', {'form': self})
                if item.stage != 'cwcSubmit':
                    messages.add_message(request, messages.ERROR, u'状态异常')
                    return render(request, 'FiProcess/cwc.html', {'form': self})
                item.cwcDealer = staff
                item.stage = 'cwcChecking'
                dateStr = request.POST['submitDate'] + ' ' + request.POST['submitHour']
                try:
                    submitTime = datetime.strptime(dateStr, '%Y-%m-%d %H')
                except:
                    messages.add_message(request, messages.ERROR, u'日期格式错误')
                    return render(request, 'FiProcess/cwc.html', {'form': self})
                item.cwcSubmitDate = submitTime
                item.save()
            if name.startswith('dealWith'):
                try:
                    item = FiStream.objects.get(id=name[8:])
                except:
                    messages.add_message(request, messages.ERROR, u'处理失败')
                    return render(request, 'FiProcess/cwc.html', {'form': self})
                if item.stage != 'cwcChecking':
                    messages.add_message(request, messages.ERROR, u'状态异常')
                    return render(request, 'FiProcess/cwc.html', {'form': self})
                item.stage = 'cwcpaid'
                item.save()
                return HttpResponseRedirect(reverse('cwc'))
            if name.startswith('checkStreamDetail'):
                try:
                    item = FiStream.objects.get(id=name[17:])
                except:
                    messages.add_message(request, messages.ERROR, u'操作失败')
                    return render(request, 'FiProcess/cwc.html', {'form': self})
                request.session['streamId'] = item.id
                return HttpResponseRedirect(reverse('index', args={'streamDetail'}))
        return render(request, 'FiProcess/cwc.html', {'form': self})
