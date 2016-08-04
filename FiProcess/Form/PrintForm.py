# -*- coding: utf-8 -*-
from django import forms
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.contrib import messages

from ..models import FiStream
from CommonStreamDetail import CommonStreamDetail
from TravelStreamDetail import TravelStreamDetail
from LaborStreamForm import LaborStreamForm
from ReceptApprovalForm import ReceptApprovalForm
from ContractApprovalForm import ContractApprovalForm


class PrintForm(forms.Form):
    def get(self, request, target):
        try:
            stream = FiStream.objects.get(number=target)
        except:
            messages.add_message(request, messages.ERROR, u'打印失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        form = None
        if stream.streamType == 'common':
            form = CommonStreamDetail()
        if stream.streamType == 'travel' or stream.streamType == 'travelApproval':
            form = TravelStreamDetail()
        if stream.streamType == 'labor':
            form = LaborStreamForm()
        if stream.streamType == 'receptApproval':
            form = ReceptApprovalForm()
        if stream.streamType == 'contractApproval':
            form = ContractApprovalForm()
        if not form:
            messages.add_message(request, messages.ERROR, u'打印失败')
            return HttpResponseRedirect(reverse('index', args={''}))
        return form.printStream(request, stream)
