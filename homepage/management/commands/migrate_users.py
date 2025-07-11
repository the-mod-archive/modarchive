from django.core.management.base import BaseCommand
from django.core.management import CommandError
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.contrib.auth.models import Group
from homepage import legacy_models
from homepage.models import Profile
from artists.models import Artist
from .disable_signals import DisableSignals

User = get_user_model()

# Recommended order for migration:
# 0. --create_groups
# 1. --migrate_users
# 2. --migrate_files
# 3. --migrate_artist_mappings_real
# 4. --migrate_favorites
# 5. --migrate_comments
# 6. --migrate_files_new
# 7. --migrate_nominations
# 8. --migrate_files_uploader
#
# --update_artist_search_indexes --all
# --update_song_search_indexes --all
#
# --convert_bbcode --comments
# --convert_bbcode --artist_comments
# --convert_bbcode --profile_blurbs
class Command(BaseCommand):
    help = "Migrates the legacy users table"

    def handle(self, *args, **options):
        with DisableSignals():
            users = legacy_models.Users.objects.using('legacy').all().order_by('userid')
            total = len(users)

            try:
                standard_group = Group.objects.get(name='Standard')
                screener_group = Group.objects.get(name='Screeners')
                artist_group = Group.objects.get(name='Artists')
                admin_group = Group.objects.get(name='Admins')
            except Group.DoesNotExist as e:
                raise CommandError(f"Missing required group: {e}") from e

            print(f"Starting migrations of {total} users. This process will create all user, profile, and artist objects.")
            counter = 0

            for user in users:
                counter += 1
                if counter % 1000 == 0:
                    print(f"Generated {counter} out of {total} from the legacy users table.")
                new_user = self.generate_user(user, admin_group, screener_group)

                if not new_user:
                    continue

                new_user.groups.add(standard_group)

                new_profile = self.generate_profile(user, new_user)

                if not new_profile or not user.cred_artist == "1":
                    continue

                self.generate_artist(user, new_user, new_profile)
                new_user.groups.add(artist_group)

    def generate_user(self, legacy_user, admin_group: Group, screener_group: Group):
        username = legacy_user.username
        password = self.get_password_with_hashing_algorithm(legacy_user.profile_password)
        email = legacy_user.profile_email
        is_staff = True if legacy_user.cred_admin == "1" else False
        date_joined = legacy_user.date

        try:
            new_user = User.objects.create(username = username, password = password, email = email, date_joined = date_joined, is_staff = is_staff)
            if is_staff:
                new_user.groups.add(admin_group)
            if legacy_user.cred_filterer == "1":
                new_user.groups.add(screener_group)
            return new_user
        except IntegrityError as e:
            print(f"Could not create user {username} due to IntegrityError {str(e)}")
            return None

    def generate_profile(self, legacy_user, new_user):
        try:
            return Profile.objects.create(
                user = new_user,
                display_name = legacy_user.profile_fullname,
                blurb = legacy_user.profile_blurb,
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin,
                legacy_id = legacy_user.userid
            )
        except IntegrityError as e:
            print(f"Could not create profile for user {new_user.username} due to IntegrityError {str(e)}")
            return None

    def generate_artist(self, legacy_user, new_user, profile):
        try:
            return Artist.objects.create(
                user = new_user,
                profile = profile,
                legacy_id = legacy_user.userid,
                name = legacy_user.profile_fullname,
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin
            )
        except IntegrityError as e:
            print(f"Could not create artist for user {new_user.username} due to IntegrityError {str(e)}")
            print(f"Trying again with username {legacy_user.profile_fullname}_1 instead")

            return Artist.objects.create(
                user = new_user,
                profile = profile,
                legacy_id = legacy_user.userid,
                name = legacy_user.profile_fullname + "_1",
                create_date = legacy_user.date,
                update_date = legacy_user.lastlogin
            )

    def get_password_with_hashing_algorithm(self, password):
        if password.startswith("$2y"):
            return "bcrypt$" + password

        if password:
            return "hmac$" + password

        return password
