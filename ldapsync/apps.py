from django.apps import AppConfig
from django.contrib.auth import get_user_model
from django.db.models.signals import pre_save
from .ldap import Ldap

def set_attributes_from_ldap(sender, instance, **kwargs):
    l = Ldap()
    username = getattr(instance, instance.USERNAME_FIELD)
    attrs = l.get_attributes(username)
    for attr in attrs:
        value = attrs[attr]
        setattr(instance, attr, value)

class MainAppConfig(AppConfig):
    name = 'ldapsync'

    def ready(self):
        super(MainAppConfig, self).ready()
        User = get_user_model()
        pre_save.connect(set_attributes_from_ldap, User, dispatch_uid='hsmw_ldapsync.set_attributes_from_ldap')
