from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from homepage.forms import UpdateProfileForm

from homepage.models import Profile

class ProfileView(View):
    def get(self, request, pk):
        try:
            profile = Profile.objects.get(pk = pk)
        except Profile.DoesNotExist:
            raise Http404("Profile does not exist")
        return render(request, 'profile.html', {'profile': profile})

class UpdateProfileView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            profile = request.user.profile
            form = UpdateProfileForm(instance=profile)
            return render(request, 'update_profile.html', {'form': form, 'profile': profile})
        except Profile.DoesNotExist:
            raise Http404("Profile does not exist")

    def post(self, request):
        try:
            profile = request.user.profile
            form = UpdateProfileForm(request.POST, instance=profile)
            form.save()
            return redirect(reverse('view_profile', kwargs = {'pk': 1}))
        except Profile.DoesNotExist:
            raise Http404("Profile does not exist")
