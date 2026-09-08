from django.db import models


class USMUser(models.Model):
    pin = models.IntegerField(null=False, blank=False)
    email = models.EmailField(null=False, blank=False)
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True)
    checked = models.BooleanField(default=False) # If the user's pin was looked upon
