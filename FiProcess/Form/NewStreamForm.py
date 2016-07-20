# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from CommonStreamForm import CommonStreamForm
from CommonStreamDetail import CommonStreamDetail

from ..models import FiStream


class NewStreamForm(forms.Form):
    def get(self, request):
        if 'streamId' in request.session:
            form = CommonStreamForm(request.GET)
            return form.modify(request)
        return render(request, 'FiProcess/newStream.html')

    def newFiStreamType(self, request):
        streamType = request.POST['newStreamType']
        if streamType == 'common':
            form = CommonStreamForm(request.POST)
            return form.get(request)
        if streamType == 'travel':
            return render(request, 'FiProcess/travelStream.html')
        if streamType == 'labor':
            return render(request, 'FiProcess/laborStream.html')
        return render(request, 'FiProcess/newStream.html')

    def post(self, request):
        if "newStreamType" in request.POST:
            return self.newFiStreamType(request)
        if "commonStreamForm" in request.POST:
            form = CommonStreamForm(request.POST)
            return form.post(request)
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
        if (stream.streamType == 'travelApproval'or stream.streamType == 'receptApproval'or stream.streamType == 'contractApproval'):
            return HttpResponseRedirect(reverse('index', args={'approvalDetail'}))
        return HttpResponseRedirect(reverse('index', args={''}))

    def postDetail(self, request):
        if 'streamId' not in request.session:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        if 'modifyStream' in request.POST:
            return HttpResponseRedirect(reverse('index', args={'newstream'}))
        streamId = request.session['streamId']
        del request.session['streamId']
        try:
            stream = FiStream.objects.get(id=streamId)
        except:
            messages.add_message(request, messages.ERROR, u'查找报销单失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        if 'createStream' in request.POST:
            if stream.streamType == 'common':
                detail = CommonStreamDetail(request.POST)
                return detail.post(request, stream)
        return HttpResponseRedirect(reverse('index', args={''}))
