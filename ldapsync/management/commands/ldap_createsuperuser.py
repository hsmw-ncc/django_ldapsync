import getpass
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = "Used to create a superuser without a usable password."

    # This command is reused for creating staff-only users (ldap_createstaffuser),
    # so this flag controls wether the superuser privilege is granted or not.
    # The `is_staff` privilege is always granted.
    GRANT_SUPERUSER_PRIVILEGES = True

    def add_arguments(self, parser):
        parser.add_argument('--username', dest='username', metavar='USERNAME', nargs='?', help='Specifies the login for the superuser.')

    def handle(self, **options):
        User = get_user_model()

        #verbosity = options.get()
        username = options.get('username')
        if not username:
            current_user = getpass.getuser()
            input_user = input('Username [{}]: '.format(current_user))
            if not input_user:
                username = current_user
            else:
                username = input_user

        obj, created = User.objects.get_or_create(username=username)
        obj.is_staff = True
        if self.GRANT_SUPERUSER_PRIVILEGES:
            privilege = "superuser"
            obj.is_superuser = True
        else:
            privilege = "staff"


        if created:
            obj.set_unusable_password()
            obj.save()
            self.stdout.write("Created user %s with %s privileges." % (username, privilege))
        else:
            obj.save()
            self.stdout.write("Granted %s privileges to user %s." % (privilege, username))

