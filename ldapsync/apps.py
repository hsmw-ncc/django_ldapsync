from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from .ldap import Ldap

def set_attributes_from_ldap(sender, instance, **kwargs):
    ''' Gets Attributes from LDAP ands Sync with user '''

    ldap = Ldap()
    username = getattr(instance, instance.USERNAME_FIELD)
    attributes = ldap.get_django_attributes_for_user(username)
    for key, value in attributes.items():
        setattr(instance, key, value)

class MainAppConfig(AppConfig):
    name = 'django_ldapsync'

    def ready(self):
        super(MainAppConfig, self).ready()
        User = get_user_model()
        pre_save.connect(set_attributes_from_ldap, User, dispatch_uid='django_ldapsync.set_attributes_from_ldap')
