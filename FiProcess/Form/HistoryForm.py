# -*- coding: utf-8 -*-
from django import forms
from django.shortcuts import render
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib import messages


class HistoryForm(forms.Form):
    def get(self, request):
        return render(request, 'FiProcess/history.html')

    def post(self, request):
        return render(request, 'FiProcess/history.html')
