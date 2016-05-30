from django.shortcuts import render, render_to_response
from django.template.context import RequestContext  

from Form.LoginForm import LoginForm

# Create your views here.

def error(request):
    return render_to_response('FiProcess/error.html')

def login(request): 
    if request.method == 'GET':  
        form = LoginForm()  
        return render_to_response('FiProcess/login.html', RequestContext(request, {'form': form,}))  
    else:  
        form = LoginForm(request.POST)  
        if form.is_valid():  
            username = request.POST.get('username', '')  
            password = request.POST.get('password', '')  
            #user = auth.authenticate(username=username, password=password) 
            user = None 
            if user is not None and user.is_active:  
                #auth.login(request, user)  
                return render_to_response('FiProcess/index.html', RequestContext(request, {'form': form,}))  
            else:  
                return render_to_response('FiProcess/login.html', RequestContext(request, {'form': form,'password_is_wrong':True}))  
        else:  
            return render_to_response('FiProcess/login.html', RequestContext(request, {'form': form,}))