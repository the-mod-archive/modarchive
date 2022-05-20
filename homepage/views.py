from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, PasswordChangeView, PasswordResetConfirmView, PasswordResetView, PasswordResetCompleteView
from django.contrib.sites.shortcuts import get_current_site
from django.db import transaction
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.urls import reverse, reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views import View
from django.views.generic.base import TemplateView, RedirectView
import json

from homepage.forms import ChangePasswordForm, CsvUploadForm, EmailAddressInUseError, ForgotPasswordForm, LoginForm, RegisterUserForm, ResetPasswordForm
from homepage.functions import is_recaptcha_success
from homepage.tokens import account_activation_token
from homepage.models import Profile
from songs.models import Song, SongStats
from artists.models import Artist

class RedirectAuthenticatedUserMixin:
    def dispatch(self, request, *args, **kwargs):
        if (request.user.is_authenticated):
            return redirect("home")
        
        return super().dispatch(request, *args, **kwargs)

def home(request):
    return render(request, 'home_page.html')

def page_not_found_view(request, exception):
    return render(request, '404.html')

@login_required
def profile(request):
    return render(request, 'account_management/profile.html')

def register(request):
    # Logged-in users should not be able to view the registration page or submit a request.
    if (request.user.is_authenticated):
        return redirect("home")

    if request.method == 'POST':
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            if not is_recaptcha_success(request.POST.get('g-recaptcha-response')):
                return redirect("register_fail")

            try:
                user = form.save()
                subject = "Active your ModArchive account"

                message = render_to_string('registration/account_activation_email.html', {
                    'user': user,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': account_activation_token.make_token(user),
                    'domain': get_current_site(request).domain
                })

                user.email_user(subject, message, 'donotreply@modarchive.org')
                return redirect("register_done")

            except EmailAddressInUseError:
                user = User.objects.get(email = form.cleaned_data['email'])
                subject = "ModArchive security warning"
                message = "A user attempted to register a ModArchive account with your email address."
                user.email_user(subject, message, 'donotreply@modarchive.org')
                return redirect("register_done")
            
        else:
            return render(request=request, template_name='registration/register.html', context={"form":form})

    form = RegisterUserForm
    return render(request, 'registration/register.html', context={'form': form, 'recaptcha_site_key': settings.GOOGLE_RECAPTCHA_SITE_KEY})

def password_reset_done(request):
    return render(request, 'password_reset/password_reset_done.html')

class LoginView(LoginView):
    template_name = 'account_management/login.html'
    form_class = LoginForm
    redirect_authenticated_user = True
    
    def get_success_url(self) -> str:
        '''
        Extension of get_success_url to implement remember me. If checkbox is not selected, user gets a normal 
        session id that expires when the browser closes.
        '''
        if not self.request.POST.get('remember_me'):
            self.request.session.set_expiry(0)

        return super().get_success_url()

class PasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    template_name = 'account_management/change_password.html'
    form_class = ChangePasswordForm
    success_url = reverse_lazy('profile')
    login_url='login'

class PasswordResetView(RedirectAuthenticatedUserMixin, PasswordResetView):
    template_name = 'password_reset/forgot_password.html'
    form_class = ForgotPasswordForm
    email_template_name = 'password_reset/password_reset_email.html'
    subject_template_name = 'password_reset/password_reset_email_subject.txt'
    from_email = 'donotreply@modarchive.org'

class PasswordResetConfirmView(RedirectAuthenticatedUserMixin, PasswordResetConfirmView):
    template_name = 'password_reset/reset_password.html'
    form_class=ResetPasswordForm

class PasswordResetCompleteView(RedirectAuthenticatedUserMixin, PasswordResetCompleteView):
    template_name='password_reset/password_reset_complete.html'

class AccountActivationCompleteView(RedirectAuthenticatedUserMixin, TemplateView):
    template_name = 'registration/account_activation_complete.html'

@transaction.atomic
def activate(request, uidb64, token):
    if (request.user.is_authenticated):
        return redirect("home")

    User = get_user_model()
    try:  
        uid = force_str(urlsafe_base64_decode(uidb64))  
        user = User.objects.get(pk=uid)  
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is None:
        return redirect('activation_error')
    elif user.is_active:
        # Take no action if user is already active
        return redirect('home')
    
    user.is_active = True
    user.save()
    Profile.objects.create(user = user, display_name = user.username)
    return redirect('account_activation_complete')

class LegacyUrlRedirectionView(RedirectView):
    redirection_map = {
        'login': {
            'log_in': 'login'
        },
        'assistance': {
            'create_account_page': 'register',
            'forgot_password_page': 'forgot_password'
        },
        'interactive': {
            'change_password_page': 'change_password'
        },
        'index': {
            'view_by_moduleid': 'view_song'
        },
        'default': {
            'default': 'home'
        }
    }

    def get_redirect_url(self, *args, **kwargs):
        php_reference = kwargs.get('php_file', 'default')
        param = self.request.GET.get('request', 'default').lower()

        redirect_target = self.redirection_map.get(php_reference).get(param, 'home')

        kwargs = {}
        if (redirect_target == 'view_song'):
            legacy_module_id = self.request.GET.get('query')
            
            try:
                song = Song.objects.get(legacy_id = legacy_module_id)
                if song:
                    kwargs['pk'] = song.id
            except:
                redirect_target = 'home'

        return reverse(redirect_target, kwargs=kwargs)

@method_decorator(login_required, name = 'dispatch')
@method_decorator(user_passes_test(lambda u: u.is_superuser, redirect_field_name=None), name = 'dispatch')
class BulkUploadView(View):
    def add_hashing_algorithm_to_password(self, password):
        if password.startswith("$2y"):
            return "bcrypt$" + password
        
        if password:
            return "hmac$" + password

        return password

    def generate_user(self, item):
        # Generate user
        username = item['username']
        password = self.add_hashing_algorithm_to_password(item['profile_password'])
        email = item['profile_email']
        is_staff = True if item['cred_admin'] else False
        date_joined = item['date']

        user = User.objects.create(username = username, password = password, email = email, date_joined = date_joined, is_staff = is_staff)

        # Generate profile
        profile = Profile.objects.create(
            user = user, 
            display_name = username, 
            blurb = item['profile_blurb'], 
            create_date = date_joined, 
            update_date = item['lastlogin'], 
            legacy_id = item['userid']
        )

        # Generate artist
        if item['cred_artist']:
            artist = Artist.objects.create(
                user = user,
                legacy_id = item['userid'],
                name = username,
                create_date = date_joined,
                update_date = item['lastlogin']
            )

        return {'artist': artist, 'user': user, 'profile': profile}

    def get_format(self, format):
        match format:
            case 'it':
                return Song.Formats.IT
            case 's3m':
                return Song.Formats.S3M
            case 'mod':
                return Song.Formats.MOD
            case 'xm':
                return Song.Formats.XM
        return None

    def get_license(self, license):
        match license:
            case 'publicdomain':
                return Song.Licenses.PUBLIC_DOMAIN
            case 'by-nc':
                return Song.Licenses.NON_COMMERCIAL
            case 'by-nc-nd':
                return Song.Licenses.NON_COMMERCIAL_NO_DERIVATIVES
            case 'by-nc-sa':
                return Song.Licenses.NON_COMMERCIAL_SHARE_ALIKE
            case 'by-nd':
                return Song.Licenses.NO_DERIVATIVES    
            case 'by-sa':
                return Song.Licenses.SHARE_ALIKE
            case 'by':
                return Song.Licenses.ATTRIBUTION
            case 'cc0':
                return Song.Licenses.CC0
        return ''

    def generate_songs(self, file):
        # Generate song
        
        format = self.get_format(file['format'])
        license = self.get_license(file['license'])

        song = Song.objects.create(
            legacy_id = file['id'], 
            filename = file['filename'], 
            title = file['songtitle'], 
            format = format,
            file_size = file['filesize'],
            channels = file['channels'],
            instrument_text = file['insttext'],
            comment_text = file['comment'],
            hash = file['hash'],
            pattern_hash = file['patternhash'],
            license = license,
            create_date = file['date'],
            update_date = file['timestamp'],
        )

        # Generate song stats
        stats = SongStats.objects.create(
            song = song,
            downloads = file['hits'],
            total_comments = file['comment_total'],
            average_comment_score = file['comment_score'],
            total_reviews = file['review_total'],
            average_review_score = file['review_score'],
        )

        # Associate with user?
        return {'song': song, 'stats': stats}

    def map_songs_to_users(self, mapping):
        # Get the artist
        artist = Artist.objects.get(legacy_id = mapping['artist'])

        # Get the song
        song = Song.objects.get(filename = mapping['filename'])

        # Associate them
        pass

    def post(self, request):
        form = CsvUploadForm(request.POST)
        if form.is_valid:
            uploaded_csv = request.FILES['csv_file'].read()
            file_data = uploaded_csv.decode("utf-8")

            json_data = json.loads(file_data)
            user_data = json_data['users']
            song_data = json_data['files']
            mapping_data = json_data['file_mappings']

            users = []
            profiles = []
            artists = []
            songs = []
            song_stats = []

            for item in user_data:
                values = self.generate_user(item)
                users.append(values['user'])
                profiles.append(values['profile'])
                artists.append(values['artist'])

            for item in song_data:
                values = self.generate_songs(item)
                songs.append(values['song'])
                song_stats.append(values['stats'])

            for item in mapping_data:
                filtered_artists = [x for x in artists if x.legacy_id == item['artist']]
                filtered_songs = [x for x in songs if x.filename == item['filename']]

                if (len(filtered_artists) != 1 or len(filtered_songs) != 1):
                    continue
                
                # TODO: Fix issue here where there is an out of range exception
                artist = filtered_artists[0]
                song = filtered_songs[0]

                song.artist_set.add(artist)

                pass
                # self.map_songs_to_users(item)

        return render(request, 'custom_admin/bulk_upload.html', context={'form': form})
    
    def get(self, request):
        form = CsvUploadForm()
        return render(request, 'custom_admin/bulk_upload.html', context={'form': form})