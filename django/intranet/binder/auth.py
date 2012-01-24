from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from models import IntranetUser

class IntranetUserBackend(ModelBackend):
    """
    Authenticates against binder.models.IntranetUser
    """
    supports_object_permissions = False
    supports_anonymous_user = True
    supports_inactive_user = True

    # TODO: Model, login attribute name and password attribute name should be
    # configurable.
    def authenticate(self, username=None, password=None):
        try:
            user = IntranetUser.objects.get(username=username)
        except IntranetUser.DoesNotExist:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
                
        if user.check_password(password):
            return user

    def get_user(self, user_id):
        try:
            return IntranetUser.objects.get(pk=user_id)
        except IntranetUser.DoesNotExist:
            try:
                return User.objects.get(pk=user_id)
            except User.DoesNotExist:
                return None
