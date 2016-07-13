# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render

from CommonStreamForm import CommonStreamForm


class NewStreamForm(forms.Form):
    def get(self, request):
        if 'orderId' in request.session:
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
