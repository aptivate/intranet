from django.db import models

from django.contrib.auth.models import User, get_hexdigest
import documents.models

# class UserProfile(models.Model):
class IntranetUser(User):
    # This field is required.
    # user = models.OneToOneField(User)

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
    program = models.ForeignKey(documents.models.Program, blank=True, null=True)
    cell_phone = models.CharField(max_length=30)
    office_location = models.CharField(max_length=1, choices=OFFICE_LOCATIONS)
    photo = models.ImageField(upload_to='profile_photos')
    # date_joined = models.DateField(blank=True)
    date_left = models.DateField(blank=True, null=True)
    
    def get_full_name(self):
        return self.full_name

    def hash_password(self, raw_password):
        if raw_password is None:
            return None
        else:
            import random
            algo = 'sha1'
            salt = get_hexdigest(algo, str(random.random()), str(random.random()))[:5]
            hsh = get_hexdigest(algo, salt, raw_password)
            return '%s$%s$%s' % (algo, salt, hsh)

    def set_password(self, raw_password):
        if raw_password is None:
            self.set_unusable_password()
        else:
            self.password = self.hash_password(raw_password)

"""
from django.db.models.signals import post_save

def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

post_save.connect(create_user_profile, sender=User)
"""
