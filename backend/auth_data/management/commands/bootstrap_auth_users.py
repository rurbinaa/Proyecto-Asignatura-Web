from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand

from media_data.models import InspectionData, RevisionDefect


class Command(BaseCommand):
    help = 'Seed expected auth users and remove legacy bootstrap users'

    LEGACY_USER_REASSIGNMENTS = {
        'admin': 'admin@uniwell.com',
        'inspector1': 'operator@uniwell.com',
        'inspector2': 'operator@uniwell.com',
        'supervisor': 'gerente@uniwell.com',
    }

    def handle(self, *args, **options):
        removed_count = 0
        reassigned_inspections = 0
        reassigned_defects = 0

        call_command('seed_auth_users', verbosity=options.get('verbosity', 1))

        for legacy_username, replacement_username in self.LEGACY_USER_REASSIGNMENTS.items():
            legacy_user = User.objects.filter(username=legacy_username).first()
            replacement_user = User.objects.filter(username=replacement_username).first()

            if not legacy_user or not replacement_user:
                continue

            reassigned_inspections += InspectionData.objects.filter(inspector=legacy_user).update(
                inspector=replacement_user
            )
            reassigned_defects += RevisionDefect.objects.filter(inspector=legacy_user).update(
                inspector=replacement_user
            )

        for username in self.LEGACY_USER_REASSIGNMENTS:
            deleted, _ = User.objects.filter(username=username).delete()
            if deleted:
                removed_count += 1
                self.stdout.write(f'Removed legacy user: {username}')

        self.stdout.write(self.style.SUCCESS(
            'Bootstrap complete: '
            f'reassigned {reassigned_inspections} inspections, '
            f'{reassigned_defects} revision defects, '
            f'removed {removed_count} legacy users, '
            'and ensured auth seed users exist'
        ))
