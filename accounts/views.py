from django.contrib.auth import login
from django.shortcuts import redirect, render
from .forms import SignupForm

def role_home(user):
    if user.is_staff or user.is_superuser:
        return "staff_dashboard"
    if user.role == user.Role.FARMER:
        return "dashboard"
    if user.role == user.Role.EXPERT:
        return "expert_dashboard"
    return "customer_dashboard"

def signup(request):
    form = SignupForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect(role_home(user))
    return render(request, "accounts/signup.html", {"form":form})
