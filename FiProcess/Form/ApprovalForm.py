# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render


class ApprovalForm(forms.Form):
    def get(self, request):
        return render(request, 'FiProcess/Approval.html')

    def post(self, request):
        return render(request, 'FiProcess/Approval.html')
