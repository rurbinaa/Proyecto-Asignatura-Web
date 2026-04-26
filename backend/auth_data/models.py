from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """
    Extends Django User model with role information.
    OneToOne relationship ensures one profile per user.
    """
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('operator', 'Operator'),
    ]
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text='Associated Django user'
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text='User role determining access level'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_data_userprofile'
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.email} - {self.role}"
    
    @property
    def is_manager(self):
        return self.role == 'manager'
    
    @property
    def is_operator(self):
        return self.role == 'operator'
