from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        primary_key=False,
        null=True
    )
    legacy_id=models.IntegerField(null=True)
    display_name = models.CharField(max_length=255)
    blurb = models.TextField(max_length=24000, null=True)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)

class BlacklistedDomain(models.Model):
    domain=models.CharField(max_length=255, unique=True)
    hits=models.IntegerField(default=0)
    added_by=models.ForeignKey(User, on_delete=models.RESTRICT)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)