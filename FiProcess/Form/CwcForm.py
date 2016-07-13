# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.template.context import RequestContext
from django.contrib import messages

from ..models import FiStream, Staff


class CwcForm(forms.Form):
    def renderForm(self, request):
        return render_to_response('FiProcess/cwc.html', RequestContext(request, {'form', self}))

    def getStreamList(self, dealer=''):
        streamList = []
        if dealer == '':
            querySet = FiStream.objects.filter(currentStage='cwcSubmit')
        else:
            querySet = FiStream.objects.filter(currentStage='cwcChecking', cwcDealer__username=dealer)
        typeDic = {'common': u'普通', 'travel': u'差旅', 'labor': u'劳务'}
        for item in querySet:
            stream = {}
            stream['projectName'] = item.projectName
            stream['applicante'] = item.applicante.name
            stream['supportDept'] = item.supportDept.name
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

        return self.renderForm(request)

    def post(self, request):
        if 'username' not in request.session:
            messages.add_message(request, messages.ERROR, '登录状态异常!')
            return HttpResponseRedirect(reverse('login'))
        if 'return' in request.POST:
            return HttpResponseRedirect(reverse('index', args={''}))
        querySet = FiStream.objects.filter()
        for item in querySet:
            if ('deal' + str(item.id)) in request.POST:
                try:
                    staff = Staff.objects.get(username=request.session['username'])
                except:
                    messages.add_message(request, messages.ERROR, '登录状态异常!')
                    return HttpResponseRedirect(reverse('login'))
                if item.currentStage == 'cwcSubmit':
                    item.cwcDealer = staff
                    item.currentStage = 'cwcChecking'
                    item.save()
                elif item.currentStage == 'cwcChecking':
                    item.currentStage = 'cwcpaid'
                    item.save()
                return HttpResponseRedirect(reverse('cwc'))
            if ('detail' + str(item.id)) in request.POST:
                request.session['orderId'] = item.id
                return HttpResponseRedirect(reverse('index', args={'streamDetail'}))
        return self.renderForm(request, self)
