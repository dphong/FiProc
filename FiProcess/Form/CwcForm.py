# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages

from ..models import FiStream, Staff
import IndexForm


class CwcForm(forms.Form):
    def getStreamList(self, dealer=''):
        streamList = []
        if dealer == '':
            querySet = FiStream.objects.filter(stage='cwcSubmit')
        else:
            querySet = FiStream.objects.filter(stage='cwcChecking', cwcDealer__username=dealer)
        typeDic = {'common': u'普通', 'travel': u'差旅', 'labor': u'劳务'}
        for item in querySet:
            stream = {}
            stream['projectName'] = item.projectName
            stream['applicante'] = item.applicante.name
            stream['supportDept'] = item.department.name
            stream['streamType'] = typeDic[item.streamType]
            stream['id'] = item.id
            streamList.append(stream)
        return streamList

    def get(self, request):
        if 'username' not in request.session:
            messages.add_message(request, messages.ERROR, '登录状态异常!')
            return HttpResponseRedirect(reverse('login'))
        if request.GET.get('target') == 'allStream':
            streamList = self.getStreamList()
            return JsonResponse(streamList, safe=False)
        elif request.GET.get('target') == 'myStream':
            streamList = self.getStreamList(request.session['username'])
            return JsonResponse(streamList, safe=False)
        return render(request, 'FiProcess/cwc.html', {'form': self})

    def post(self, request):
        if 'username' not in request.session:
            messages.add_message(request, messages.ERROR, '登录状态异常!')
            return HttpResponseRedirect(reverse('login'))
        if 'return' in request.POST:
            return HttpResponseRedirect(reverse('index', args={''}))
        for name, value in request.POST.iteritems():
            if name.startswith('dealWith'):
                try:
                    staff = Staff.objects.get(username=request.session['username'])
                except:
                    return IndexForm.logout(request, u'登录状态异常!')
                try:
                    item = FiStream.objects.get(id=name[8:])
                except:
                    messages.add_message(request, messages.ERROR, u'处理失败')
                    return render(request, 'FiProcess/cwc.html', {'form': self})
                if item.stage == 'cwcSubmit':
                    item.cwcDealer = staff
                    item.stage = 'cwcChecking'
                    item.save()
                elif item.stage == 'cwcChecking':
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
