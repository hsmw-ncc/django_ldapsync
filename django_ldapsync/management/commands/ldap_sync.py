import re
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django_ldapsync import Ldap

class Command(BaseCommand):
    DEFAULT_EXCLUDE_REGEX = r'^api-'
    help = "Updates the attributes of all Django users from the LDAP server."

    def add_arguments(self, parser):
        parser.add_argument('-e', '--exclude',
                dest='exclude_usernames',
                metavar='username',
                nargs='*',
                help="You can exclude single usernames from the LDAP sync using this switch."
            )
        parser.add_argument('-r', '--exclude-regex',
                default=self.DEFAULT_EXCLUDE_REGEX,
                dest='exclude_regex',
                metavar='regex',
                nargs='?',
                help="Sometimes you might want to exclude users from LDAP sync,\
                      such as API users. You may specify a Python regular expression \
                      here for usernames that you want to ignore during the sync.\n\
                      Default: \"{}\"".format(self.DEFAULT_EXCLUDE_REGEX),
            )

    def handle(self, *args, **options):
        verbosity = options.get('verbosity')
        sync_is_active = getattr(settings, 'LDAP_SYNC_DISABLE_INVALID_USER', False)

        exclude_regex = options.get('exclude_regex')
        if exclude_regex:
            exclude_regex = re.compile(exclude_regex)

        exclude_usernames = options.get('exclude_usernames')
        if exclude_usernames:
            exclude_usernames = set(exclude_usernames)
        else:
            exclude_usernames = set()

        User = get_user_model()
        ldap = Ldap()

        values = list(ldap.LDAP_SYNC_USER_ATTRIBUTES.keys())
        values.append(User.USERNAME_FIELD)
        if sync_is_active:
            values.append('is_active')

        for user_dict in User.objects.all().values(*values).iterator():
            username = user_dict[User.USERNAME_FIELD]

            if username in exclude_usernames:
                if verbosity > 2:
                    self.stdout.write('Ignoring {}'.format(username))
                continue

            if exclude_regex and exclude_regex.match(username):
                if verbosity > 2:
                    self.stdout.write('Ignoring {}'.format(username))
                continue

            attrs = ldap.get_django_attributes_for_user(username)
            if sync_is_active:
                if attrs:
                    attrs['is_active'] = True
                else:
                    attrs['is_active'] = False

            changed = False
            for attr in attrs:
                if user_dict[attr] != attrs[attr]:
                    changed = True
                    break

            if changed:
                filter_args = {User.USERNAME_FIELD: username}
                if verbosity > 1:
                    self.stdout.write('Updating %s: %s' %(username, attrs))
                User.objects.filter(**filter_args).update(**attrs)
