from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import Session, User

class SessionBookingForm(forms.ModelForm):
    """Form for booking a session with a mentor."""
    def __init__(self, *args, **kwargs):
        self.mentor_id = kwargs.pop('mentor_id', None)
        super().__init__(*args, **kwargs)
        
        # Set default duration to 30 minutes if not set
        if not self.initial.get('duration_minutes'):
            self.initial['duration_minutes'] = 30
            
        # Set minimum datetime to now
        self.fields['scheduled_time'].widget.attrs['min'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
    
    class Meta:
        model = Session
        fields = ['title', 'description', 'scheduled_time', 'duration_minutes']
        widgets = {
            'scheduled_time': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control',
                }
            ),
            'duration_minutes': forms.NumberInput(
                attrs={
                    'class': 'form-control',
                    'min': 15,
                    'max': 120,
                    'step': 15,
                }
            ),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }
        help_texts = {
            'scheduled_time': 'Select a date and time for your session',
            'duration_minutes': 'Session duration in minutes (15-120 minutes)',
        }

    def clean(self):
        cleaned_data = super().clean()
        scheduled_time = cleaned_data.get('scheduled_time')
        duration_minutes = cleaned_data.get('duration_minutes')
        
        # Validate scheduled time is in the future
        if scheduled_time and scheduled_time < timezone.now():
            self.add_error('scheduled_time', 'Scheduled time cannot be in the past.')
            
        # Validate duration is within allowed range
        if duration_minutes and (duration_minutes < 15 or duration_minutes > 120):
            self.add_error('duration_minutes', 'Duration must be between 15 and 120 minutes.')
            
        # Validate mentor exists
        if self.mentor_id:
            try:
                mentor = User.objects.get(id=self.mentor_id, is_mentor=True)
                cleaned_data['mentor'] = mentor
            except User.DoesNotExist:
                raise ValidationError('Selected mentor does not exist or is not available.')
                
        return cleaned_data
