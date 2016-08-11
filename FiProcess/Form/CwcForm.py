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

    def getStream(self, stream):
        typeDic = {'common': u'普通', 'travel': u'差旅', 'labor': u'劳务', 'travelApproval': u'差旅'}
        item = {}
        item['number'] = stream.number
        item['projectName'] = stream.projectName
        item['applicante'] = stream.applicante.name
        item['supportDept'] = stream.department.name
        item['streamType'] = typeDic[stream.streamType]
        item['time'] = stream.cwcSubmitDate.strftime('%Y-%m-%d')
        if stream.cwcSubmitDate.hour > 12:
            item['time'] += u'下午'
        else:
            item['time'] += u'上午'
        item['id'] = stream.id
        return item

    def getStreamList(self, dealer=None):
        streamList = []
        if dealer:
            querySet = FiStream.objects.filter(stage='cwcChecking', cwcDealer__id=dealer.id).order_by('cwcSubmitDate')
        else:
            querySet = FiStream.objects.filter(stage='cwcSubmit')
        for item in querySet:
            streamList.append(self.getStream(item))
        return streamList

    def getHistory(self, staff):
        streamList = []
        querySet = FiStream.objects.filter(stage='cwcpaid', cwcDealer__id=staff.id).order_by('-cwcSubmitDate')
        for item in querySet:
            streamList.append(self.getStream(item))
        return streamList

    def get(self, request):
        try:
            staff = Staff.objects.get(username=request.session['username'])
        except:
            return FormPublic.logout(request, u'登录状态异常!')
        if staff.department.name != u'财务处':
            messages.add_message(request, messages.ERROR, u'操作异常')
            return HttpResponseRedirect(reverse('index', args={''}))
        request.session['office'] = 'cwc'
        target = request.GET.get('target')
        if target:
            request.session['currentCwcTab'] = target
        if target == 'allStream':
            streamList = self.getStreamList()
            return JsonResponse(streamList, safe=False)
        elif target == 'myStream':
            streamList = self.getStreamList(staff)
            return JsonResponse(streamList, safe=False)
        elif target == 'myHistory':
            streamList = self.getHistory(staff)
            return JsonResponse(streamList, safe=False)
        target = request.session['currentCwcTab']
        if not target:
            request.session['currentCwcTab'] = 'myStream'
        return render(request, 'FiProcess/cwc.html', {'form': self, 'target': target})

    def post(self, request):
        if 'returnIndex' in request.POST:
            del request.session['office']
            del request.session['currentCwcTab']
            return HttpResponseRedirect(reverse('index', args={''}))
        try:
            staff = Staff.objects.get(username=request.session['username'])
        except:
            return FormPublic.logout(request, u'登录状态异常!')
        target = request.session['currentCwcTab']
        if not target:
            target = 'myStream'
        if staff.department.name != u'财务处':
            messages.add_message(request, messages.ERROR, u'操作异常')
            return HttpResponseRedirect(reverse('index', args={''}))
        for name, value in request.POST.iteritems():
            if name.startswith('acceptStream'):
                try:
                    item = FiStream.objects.get(id=name[12:])
                except:
                    messages.add_message(request, messages.ERROR, u'处理失败')
                    return render(request, 'FiProcess/cwc.html', {'form': self, 'target': target})
                if item.stage != 'cwcSubmit':
                    messages.add_message(request, messages.ERROR, u'状态异常')
                    return render(request, 'FiProcess/cwc.html', {'form': self, 'target': target})
                item.cwcDealer = staff
                item.stage = 'cwcChecking'
                dateStr = request.POST['submitDate'] + ' ' + request.POST['submitHour']
                try:
                    submitTime = datetime.strptime(dateStr, '%Y-%m-%d %H')
                except:
                    messages.add_message(request, messages.ERROR, u'日期格式错误')
                    return render(request, 'FiProcess/cwc.html', {'form': self, 'target': target})
                item.cwcSubmitDate = submitTime
                item.save()
            if name.startswith('dealWith'):
                try:
                    item = FiStream.objects.get(id=name[8:])
                except:
                    messages.add_message(request, messages.ERROR, u'处理失败')
                    return render(request, 'FiProcess/cwc.html', {'form': self, 'target': target})
                if item.stage != 'cwcChecking':
                    messages.add_message(request, messages.ERROR, u'状态异常')
                    return render(request, 'FiProcess/cwc.html', {'form': self, 'target': target})
                item.stage = 'cwcpaid'
                item.save()
                return HttpResponseRedirect(reverse('cwc'))
            if name.startswith('checkStreamDetail'):
                try:
                    item = FiStream.objects.get(id=name[17:])
                except:
                    messages.add_message(request, messages.ERROR, u'操作失败')
                    return render(request, 'FiProcess/cwc.html', {'form': self, 'target': target})
                request.session['streamId'] = item.id
                return HttpResponseRedirect(reverse('index', args={'streamDetail'}))
        return render(request, 'FiProcess/cwc.html', {'form': self, 'target': target})
