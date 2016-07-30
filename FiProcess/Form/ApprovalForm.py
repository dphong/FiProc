# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from ..models import FiStream
from TravelApprovalForm import TravelApprovalForm
from ReceptApprovalForm import ReceptApprovalForm
from ContractApprovalForm import ContractApprovalForm


class ApprovalForm(forms.Form):
    def get(self, request):
        return render(request, 'FiProcess/Approval.html')

    def post(self, request):
        if 'approvalType' in request.POST:
            if 'travel' == request.POST['approvalType']:
                form = TravelApprovalForm(request.POST)
                return form.getPost(request)
            if 'recept' == request.POST['approvalType']:
                form = ReceptApprovalForm(request.POST)
                return form.getPost(request)
            if 'contract' == request.POST['approvalType']:
                form = ContractApprovalForm(request.POST)
                return form.getPost(request)
        if 'createApprovalTravel' in request.POST:
            form = TravelApprovalForm(request.POST)
            return form.post(request)
        if 'submitApprovalTravel' in request.POST:
            form = TravelApprovalForm(request.POST)
            return form.submitPost(request)
        if 'receptForm' in request.POST:
            form = ReceptApprovalForm(request.POST)
            return form.post(request)
        if 'contractForm' in request.POST:
            form = ContractApprovalForm(request.POST)
            return form.post(request)
        return render(request, 'FiProcess/Approval.html')

    def getDetail(self, request):
        if 'streamId' not in request.session:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        try:
            stream = FiStream.objects.get(id=request.session['streamId'])
        except:
            messages.add_message(request, messages.ERROR, u'操作失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        if stream.streamType == 'travelApproval':
            form = TravelApprovalForm(request.GET)
            return form.detail(request, stream)
        if stream.streamType == 'receptApproval':
            form = ReceptApprovalForm(request.GET)
            return form.detail(request, stream)
        if stream.streamType == 'contractApproval':
            form = ContractApprovalForm(request.GET)
            return form.detail(request, stream)

    def postDetail(self, request):
        if 'TravelRecord' in request.session:
            form = TravelApprovalForm(request.POST)
            return form.submitPost(request)
        return HttpResponseRedirect(reverse('index', args={''}))
