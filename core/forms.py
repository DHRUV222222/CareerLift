from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.forms import inlineformset_factory
from .models import User, Mentor, Project, Resume, Feedback, Availability, Session

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your email address',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'required': 'required'
        })
    )
    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'First name',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'required': 'required'
        })
    )
    last_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Last name',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'required': 'required'
        })
    )
    username = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose a username',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'required': 'required'
        })
    )
    password1 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a password',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'required': 'required'
        })
    )
    password2 = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
            'required': 'required'
        })
    )
    is_mentor = forms.BooleanField(
        required=False, 
        label='Register as a mentor',
        help_text='Check this if you want to register as a mentor.',
        widget=forms.CheckboxInput(attrs={
            'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_mentor']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to form fields
        for field_name, field in self.fields.items():
            if field_name == 'username':
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                    'placeholder': 'Choose a username'
                })
            elif field_name in ['password1', 'password2']:
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500',
                    'placeholder': '••••••••'
                })
    
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise forms.ValidationError('First name is required.')
        if not first_name.replace(' ', '').isalpha():
            raise forms.ValidationError('First name should only contain letters and spaces.')
        return first_name
        
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise forms.ValidationError('Last name is required.')
        if not last_name.replace(' ', '').isalpha():
            raise forms.ValidationError('Last name should only contain letters and spaces.')
        return last_name
        
    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if not username:
            raise forms.ValidationError('Username is required.')
        if len(username) < 4:
            raise forms.ValidationError('Username must be at least 4 characters long.')
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError('A user with that username already exists.')
        return username
    
    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip()
        if not email:
            raise forms.ValidationError('Email is required.')
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.is_mentor = self.cleaned_data['is_mentor']
        user.is_student = not user.is_mentor  # Set is_student to False if user is a mentor
        
        if commit:
            user.save()
            # If user is a mentor, create a mentor profile
            if user.is_mentor:
                Mentor.objects.get_or_create(
                    user=user,
                    defaults={'bio': ''}  # Empty bio by default
                )
        return user

class UserLoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'

class UserUpdateForm(forms.ModelForm):
    first_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'required': 'required'
        })
    )
    last_name = forms.CharField(
        required=True,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'required': 'required'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
            'required': 'required'
        })
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'bio', 'profile_picture']
        widgets = {
            'bio': forms.Textarea(attrs={
                'rows': 3,
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            }),
            'phone': forms.TextInput(attrs={
                'placeholder': 'Enter your phone number',
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Tailwind classes to profile picture field
        self.fields['profile_picture'].widget.attrs.update({
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            'accept': 'image/*'
        })
        
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if not first_name:
            raise forms.ValidationError('First name is required.')
        if not first_name.replace(' ', '').isalpha():
            raise forms.ValidationError('First name should only contain letters and spaces.')
        return first_name
        
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if not last_name:
            raise forms.ValidationError('Last name is required.')
        if not last_name.replace(' ', '').isalpha():
            raise forms.ValidationError('Last name should only contain letters and spaces.')
        return last_name
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError('This email is already in use. Please use a different email address.')
        return email

class TimeInput(forms.TimeInput):
    input_type = 'time'
    input_format = '%H:%M'

class AvailabilityForm(forms.ModelForm):
    DAY_CHOICES = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    day_of_week = forms.ChoiceField(choices=DAY_CHOICES)
    start_time = forms.TimeField(widget=TimeInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}))
    end_time = forms.TimeField(widget=TimeInput(attrs={'class': 'w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}))
    is_recurring = forms.BooleanField(
        required=False, 
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'})
    )
    DELETE = forms.BooleanField(
        required=False,
        widget=forms.HiddenInput(attrs={'class': 'delete'}),
        label=''
    )

    class Meta:
        model = Availability
        fields = ['day_of_week', 'start_time', 'end_time', 'is_recurring', 'DELETE']

    def clean(self):
        cleaned_data = super().clean()
        
        # Skip validation if marked for deletion
        if cleaned_data.get('DELETE'):
            return cleaned_data
        
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time and start_time >= end_time:
            raise forms.ValidationError('End time must be after start time.')

        return cleaned_data


class MentorProfileForm(forms.ModelForm):
    class Meta:
        model = Mentor
        fields = ['title', 'company', 'bio', 'linkedin_url', 'is_available']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': 'e.g., Senior Software Engineer'}),
            'company': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': 'e.g., Tech Company Inc.'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'placeholder': 'https://linkedin.com/in/yourprofile'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'}),
        }


class SessionForm(forms.ModelForm):
    """Form for managing mentorship sessions."""
    class Meta:
        model = Session
        fields = ['title', 'description', 'scheduled_time', 'duration_minutes', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
            'scheduled_time': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}, format='%Y-%m-%dT%H:%M'),
            'duration_minutes': forms.NumberInput(attrs={'class': 'mt-1 block w-24 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500', 'min': '15', 'step': '15'}),
            'status': forms.Select(attrs={'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set initial scheduled time to next hour if not set
        if not self.instance.pk:
            next_hour = timezone.now().replace(minute=0, second=0, microsecond=0) + timezone.timedelta(hours=1)
            self.initial.setdefault('scheduled_time', next_hour.strftime('%Y-%m-%dT%H:%M'))

    def clean_scheduled_time(self):
        scheduled_time = self.cleaned_data.get('scheduled_time')
        if scheduled_time and scheduled_time < timezone.now():
            raise ValidationError(_("Scheduled time cannot be in the past."))
        return scheduled_time

    def clean_duration_minutes(self):
        duration = self.cleaned_data.get('duration_minutes')
        if duration and (duration < 15 or duration > 120):
            raise ValidationError(_("Duration must be between 15 and 120 minutes."))
        return duration


# Formset for managing multiple availability slots
class CustomInlineFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        # Check that at least one time slot is provided
        if any(self.errors):
            return
            
        # Check that we have at least one form that's not marked for deletion
        count = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                count += 1
                
        if count < 1:
            raise forms.ValidationError('You must have at least one availability slot.')


# Create a base formset with delete field
BaseAvailabilityFormSet = inlineformset_factory(
    Mentor, 
    Availability, 
    form=AvailabilityForm,
    formset=CustomInlineFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    fields=('day_of_week', 'start_time', 'end_time', 'is_recurring', 'id')
)

# Custom formset that includes the DELETE field
class AvailabilityFormSet(BaseAvailabilityFormSet):
    def add_fields(self, form, index):
        super().add_fields(form, index)
        if 'DELETE' in form.fields:
            form.fields['DELETE'].widget = forms.HiddenInput()
            form.fields['DELETE'].label = ''

# Create the final formset
AvailabilityFormSet = inlineformset_factory(
    Mentor,
    Availability,
    form=AvailabilityForm,
    formset=AvailabilityFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
    fields=('day_of_week', 'start_time', 'end_time', 'is_recurring', 'id')
)
