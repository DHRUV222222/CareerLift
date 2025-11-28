from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.core.validators import FileExtensionValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
import datetime

class User(AbstractUser):
    """Custom user model that extends Django's built-in User model."""
    is_student = models.BooleanField(default=True)
    is_mentor = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    phone = models.CharField(max_length=20, blank=True, null=True, help_text='Contact phone number')
    
    def __str__(self):
        return self.username

class Availability(models.Model):
    """Weekly availability slots for mentors."""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    mentor = models.ForeignKey('Mentor', on_delete=models.CASCADE, related_name='availability_slots')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_recurring = models.BooleanField(default=True, help_text='If checked, this slot repeats every week')
    
    class Meta:
        verbose_name_plural = 'Availabilities'
        ordering = ['day_of_week', 'start_time']
    
    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time.strftime('%H:%M')}-{self.end_time.strftime('%H:%M')}"
    
    def clean(self):
        if self.start_time is None or self.end_time is None:
            raise ValidationError('Both start time and end time are required')
            
        if self.start_time >= self.end_time:
            raise ValidationError('End time must be after start time')
        
        # Check for overlapping slots
        if not self.mentor_id:  # Skip overlap check if mentor is not set yet
            return
            
        overlapping = Availability.objects.filter(
            mentor=self.mentor,
            day_of_week=self.day_of_week,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(pk=self.pk if self.pk else None)
        
        if overlapping.exists():
            raise ValidationError('This time slot overlaps with an existing availability slot')


class Mentor(models.Model):
    """Mentor profile that extends the User model."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True, related_name='mentor_profile')
    title = models.CharField(max_length=100, blank=True, null=True, verbose_name='Job Title')
    company = models.CharField(max_length=100, blank=True, null=True, verbose_name='Current Company')
    bio = models.TextField(max_length=1000, blank=True)
    linkedin_url = models.URLField(blank=True, null=True, verbose_name='LinkedIn Profile')
    is_available = models.BooleanField(default=True, help_text='Global availability toggle')
    
    # Deprecated - kept for backward compatibility
    availability = models.BooleanField(default=True, editable=False)
    
    def save(self, *args, **kwargs):
        # Keep the old availability field in sync with is_available
        self.availability = self.is_available
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} (Mentor)"
        
    @property
    def session_requests(self):
        """Return all pending session requests for this mentor."""
        return self.user.mentor_sessions.filter(status='requested')
        
    @property
    def upcoming_sessions(self):
        """Return all upcoming accepted sessions."""
        return self.user.mentor_sessions.filter(
            status='accepted',
            scheduled_time__gt=timezone.now()
        ).order_by('scheduled_time')
        
    @property
    def completed_sessions(self):
        """Return all completed sessions."""
        return self.user.mentor_sessions.filter(
            status='completed'
        ).order_by('-scheduled_time')
        
    @property
    def mentor_sessions(self):
        """Return all sessions for this mentor."""
        return self.user.mentor_sessions.all()

class Project(models.Model):
    """Projects created by students."""
    title = models.CharField(max_length=200)
    description = models.TextField()
    tech_stack = models.CharField(max_length=200, help_text="Technologies used (comma-separated)")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='projects')
    
    def __str__(self):
        return self.title
        
    def get_tech_stack_list(self):
        """Return tech stack as a list of strings."""
        if not self.tech_stack:
            return []
        # Split by comma and clean up whitespace
        return [tech.strip() for tech in self.tech_stack.split(',') if tech.strip()]

class ProjectImage(models.Model):
    """Images associated with projects."""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='project_images/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.project.title}"

class Resume(models.Model):
    """Resume files uploaded by students."""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    title = models.CharField(max_length=100)
    file = models.FileField(
        upload_to='resumes/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])]
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} - {self.student.username}"
    
    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary resume per user
            Resume.objects.filter(student=self.student, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)

class Feedback(models.Model):
    """Feedback provided by mentors on student resumes/projects."""
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_feedback')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_feedback')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Feedback from {self.mentor.username} to {self.student.username}"

class Session(models.Model):
    """1:1 mentorship sessions between students and mentors."""
    SESSION_STATUS = [
        ('requested', 'Requested'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='student_sessions')
    mentor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mentor_sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=SESSION_STATUS, default='requested')
    scheduled_time = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['scheduled_time']
    
    def __str__(self):
        return f"{self.title} - {self.student.username} with {self.mentor.username}"
