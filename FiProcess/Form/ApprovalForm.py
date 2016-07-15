# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render


class ApprovalForm(forms.Form):
    def get(self, request):
        return render(request, 'FiProcess/Approval.html')

    def post(self, request):
        if 'travel' == request.POST['approvalType']:
            return render(request, 'FiProcess/approvalTravel.html')
        if 'recept' == request.POST['approvalType']:
            return render(request, 'FiProcess/approvalRecept.html')
        if 'contract' == request.POST['approvalType']:
            return render(request, 'FiProcess/approvalContract.html')
        return render(request, 'FiProcess/Approval.html')
