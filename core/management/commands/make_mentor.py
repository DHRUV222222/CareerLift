from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from core.models import Mentor

class Command(BaseCommand):
    help = 'Mark an existing user as a mentor and create a mentor profile'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the user to make a mentor')
        parser.add_argument('--title', type=str, help='Job title for the mentor', default='')
        parser.add_argument('--company', type=str, help='Company for the mentor', default='')
        parser.add_argument('--bio', type=str, help='Bio for the mentor', default='')

    def handle(self, *args, **options):
        User = get_user_model()
        username = options['username']
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'User "{username}" does not exist')
        
        if hasattr(user, 'mentor_profile'):
            self.stdout.write(self.style.SUCCESS(f'User "{username}" is already a mentor'))
            return
        
        # Update user to be a mentor
        user.is_mentor = True
        user.save()
        
        # Create mentor profile
        Mentor.objects.create(
            user=user,
            title=options['title'],
            company=options['company'],
            bio=options['bio']
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully made "{username}" a mentor with a new profile')
        )
