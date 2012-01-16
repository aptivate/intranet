from django.db import models

from django.contrib.auth.models import User
import documents.models

class UserProfile(models.Model):
    # This field is required.
    user = models.OneToOneField(User)

    SEX_CHOICE = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    
    OFFICE_LOCATIONS = (
        ('7', '7th Floor'),
        ('8', '8th Floor'),
        ('9', '9th Floor'),
    )

    # Other fields here
    full_name = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    sex = models.CharField(max_length=1, choices=SEX_CHOICE)
    program = models.ForeignKey(documents.models.Program, blank=True)
    cell_phone = models.CharField(max_length=30)
    office_location = models.CharField(max_length=1, choices=OFFICE_LOCATIONS)
    photo = models.ImageField(upload_to='profile_photos')
    date_joined = models.DateField(blank=True)
    date_left = models.DateField(blank=True)

from django.db.models.signals import post_save

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
