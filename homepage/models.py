from django.db import models
from django.contrib.auth.models import User

class BlacklistedDomain(models.Model):
    domain=models.CharField(max_length=255, unique=True)
    hits=models.IntegerField(default=0)
    added_by=models.ForeignKey(User, on_delete=models.RESTRICT)
    create_date=models.DateTimeField(auto_now_add=True)
    update_date=models.DateTimeField(auto_now=True)