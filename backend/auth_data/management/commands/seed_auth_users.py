from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from auth_data.models import UserProfile


class Command(BaseCommand):
    help = 'Seed 6 hardcoded users with roles (idempotent)'
    
    USERS = [
        ('gerente@uniwell.com', 'manager'),
        ('gerencia@uniwell.com', 'manager'),
        ('manager@uniwell.com', 'manager'),
        ('admin@uniwell.com', 'manager'),
        ('operator@uniwell.com', 'operator'),
        ('GERENCIA@uniwell.com', 'manager'),
    ]
    
    DEFAULT_PASSWORD = '1234'
    
    def handle(self, *args, **options):
        created_count = 0
        skipped_count = 0
        
        for email, role in self.USERS:
            user, user_created = User.objects.get_or_create(
                username=email,
                defaults={
                    'email': email,
                    'first_name': '',
                    'last_name': '',
                }
            )
            
            if user_created:
                user.set_password(self.DEFAULT_PASSWORD)
                user.save()
                UserProfile.objects.create(user=user, role=role)
                created_count += 1
                self.stdout.write(f"Created: {email} ({role})")
            else:
                skipped_count += 1
                self.stdout.write(f"Skipped (exists): {email}")
        
        self.stdout.write(self.style.SUCCESS(
            f'\nComplete: {created_count} created, {skipped_count} skipped'
        ))
