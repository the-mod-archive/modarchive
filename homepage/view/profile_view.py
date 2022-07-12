from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from homepage.forms import UpdateProfileForm

from homepage.models import Profile

class ProfileView(DetailView):
    model = Profile
    template_name = 'profile.html'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if (hasattr(self.object, 'artist')):
            return redirect('view_artist', self.object.artist.id)

        return response

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
            return redirect(reverse('view_profile', kwargs = {'pk': profile.id}))
        except Profile.DoesNotExist:
            raise Http404("Profile does not exist")
