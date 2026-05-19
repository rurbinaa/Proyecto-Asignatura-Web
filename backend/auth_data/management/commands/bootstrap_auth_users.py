from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db.models.deletion import ProtectedError


class Command(BaseCommand):
    help = 'Seed expected auth users and remove legacy bootstrap users'

    LEGACY_BOOTSTRAP_USERNAMES = (
        'admin',
        'inspector1',
        'inspector2',
        'supervisor',
    )

    def handle(self, *args, **options):
        call_command('seed_auth_users', verbosity=options.get('verbosity', 1))

        deleted_usernames = []
        skipped_usernames = []

        for username in self.LEGACY_BOOTSTRAP_USERNAMES:
            user = User.objects.filter(username=username).first()
            if user is None:
                continue

            try:
                user.delete()
                deleted_usernames.append(username)
                self.stdout.write(f'Deleted legacy user: {username}')
            except ProtectedError:
                skipped_usernames.append(username)
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipped legacy user: {username} (protected reference)'
                    )
                )
            except Exception:
                skipped_usernames.append(username)
                self.stdout.write(
                    self.style.WARNING(
                        f'Skipped legacy user: {username} (unexpected error)'
                    )
                )

        deleted_count = len(deleted_usernames)
        skipped_count = len(skipped_usernames)

        deleted_part = (
            f'deleted: {deleted_count}'
            + (f' ({", ".join(deleted_usernames)})' if deleted_usernames else '')
        )
        skipped_part = (
            f'skipped: {skipped_count}'
            + (f' ({", ".join(skipped_usernames)})' if skipped_usernames else '')
        )

        self.stdout.write(self.style.SUCCESS(
            'Bootstrap complete: '
            f'{deleted_part}, {skipped_part}, '
            'and ensured auth seed users exist'
        ))
