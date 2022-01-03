from .ldap_createsuperuser import Command as SuperUserCommand

class Command(SuperUserCommand):
    help = "Used to create a staff user without a usable password."
    GRANT_SUPERUSER_PRIVILEGES = False
