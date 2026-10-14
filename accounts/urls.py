from django.contrib.auth import views as auth_views
from django.contrib import messages
from django.urls import path, reverse
from .views import role_home, signup

class FarmConnectLoginView(auth_views.LoginView):
    template_name = "accounts/login.html"
    def get_success_url(self):
        return self.get_redirect_url() or reverse(role_home(self.request.user))

class StaffLoginView(auth_views.LoginView):
    template_name = "accounts/admin_login.html"
    def form_valid(self, form):
        if not form.get_user().is_staff:
            messages.error(self.request, "This sign-in is for FarmConnect administrators. Use the community login instead.")
            return self.form_invalid(form)
        return super().form_valid(form)
    def get_success_url(self):
        return self.get_redirect_url() or reverse("staff_dashboard")

urlpatterns = [path("signup/", signup, name="signup"), path("login/", FarmConnectLoginView.as_view(), name="login"), path("admin-login/", StaffLoginView.as_view(), name="admin_login"), path("logout/", auth_views.LogoutView.as_view(), name="logout")]
