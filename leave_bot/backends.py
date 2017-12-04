from django.contrib.auth.hashers import check_password
from .models import AdminUser


class AdminUserBackend(object):

    def authenticate(self, email=None, password=None):
        try:
            user = AdminUser.objects.get(email=email)
        except AdminUser.DoesNotExist:
            return None

        if check_password(password, user.password):
            return user
        return None

    def get_user(self, user_id):
        try:
            return AdminUser.objects.get(pk=user_id)
        except AdminUser.DoesNotExist:
            return None

