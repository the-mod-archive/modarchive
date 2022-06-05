from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views import View

from artists.forms import CreateArtistForm

class AddArtistView(PermissionRequiredMixin, View):
    permission_required = 'artists.add_artist'

    def get(self, request):
        form = CreateArtistForm()
        return render(request, "add_artist.html", {'form': form})

    def post(self, request):
        form = CreateArtistForm(request.POST)
        if (form.is_valid()):
            new_artist = form.save()
            return redirect(reverse('view_artist', kwargs = {'pk': new_artist.id}))

        return render(request, "add_artist.html", {'form': form})