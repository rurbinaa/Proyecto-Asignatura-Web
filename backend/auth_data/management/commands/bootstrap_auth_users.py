from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Seed expected auth users and remove legacy bootstrap users'

    LEGACY_USER_REASSIGNMENTS = {
        'admin': 'admin@uniwell.com',
        'inspector1': 'gerente@uniwell.com',
        'inspector2': 'gerente@uniwell.com',
        'supervisor': 'gerente@uniwell.com',
    }

    def handle(self, *args, **options):
        removed_count = 0
        call_command('seed_auth_users', verbosity=options.get('verbosity', 1))

        for username in self.LEGACY_USER_REASSIGNMENTS:
            deleted, _ = User.objects.filter(username=username).delete()
            if deleted:
                removed_count += 1
                self.stdout.write(f'Removed legacy user: {username}')

        self.stdout.write(self.style.SUCCESS(
            'Bootstrap complete: '
            f'removed {removed_count} legacy users, '
            'and ensured auth seed users exist'
        ))
