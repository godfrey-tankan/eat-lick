from django.contrib.auth import authenticate, login
from django.http import HttpResponseRedirect, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.contrib.auth.forms import AuthenticationForm
from django.contrib import messages
from home.forms import CustomLoginForm

@csrf_exempt
def custom_login(request):
    if request.method == 'POST':
        form = CustomLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            # Authenticate the user
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return JsonResponse({'status': 'success', 'redirect_url': '/'}, status=200)
            else:
                messages.error(request, "Invalid username or password.")
        else:
            messages.error(request, "Please fix the errors below.")

    else:
        form = CustomLoginForm()

    return render(request, 'accounts/login.html', {'form': form})


