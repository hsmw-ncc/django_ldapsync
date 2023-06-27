from django.conf import settings
from django.contrib.auth.models import Group
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django_ldapsync import Ldap

class Command(BaseCommand):
    help = "Import LDAP-Group"

    def add_arguments(self, parser):
        parser.add_argument('-g', '--group',
          dest='group_name',
          help="Groupname"
        )

    def handle(self, *args, **options):
        ''' Import Users from LDAP-Group '''

        # Settings
        username_lower = getattr(settings, 'LDAP_SYNC_ALWAYS_LOWER_USERNAME', True)

        # Read Group-Members
        ldap = Ldap()
        group_name = options.get('group_name', None)
        group_name_dn = ldap.get_dn(group_name)
        if not group_name_dn:
          self.stdout.write(f"ERROR: Group '{group_name}' not found in LDAP")
          return
        members = ldap.get_group_members(group_name_dn)

        # Member Lookup/Creation
        User = get_user_model()
        for member in members:

          # Which Field ist the Username
          username_key = ldap.LDAP_SYNC_USER_ATTRIBUTES['username']

          # User
          username = member[username_key] if username_lower else member[username_key].lower()
          obj, created = User.objects.get_or_create(username=username)
          if created:
            obj.set_unusable_password()
            obj.save()

          # Group
          if not obj.groups.filter(name=group_name).exists():
            django_group, _ = Group.objects.get_or_create(name=group_name)
            django_group.user_set.add(obj)
