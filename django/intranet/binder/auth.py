from django.contrib.auth.backends import ModelBackend
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
            if user.check_password(password):
                return user
        except IntranetUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return IntranetUser.objects.get(pk=user_id)
        except IntranetUser.DoesNotExist:
            return None
