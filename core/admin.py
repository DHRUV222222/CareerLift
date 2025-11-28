from django.contrib import admin
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import Mentor, Project, ProjectImage, Resume, Feedback, Session, Availability

User = get_user_model()

class MentorInline(admin.StackedInline):
    model = Mentor
    can_delete = False
    verbose_name_plural = 'Mentor Profile'
    fk_name = 'user'
    extra = 0

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'full_name', 'is_student', 'is_mentor', 'is_active', 'last_login')
    list_filter = ('is_student', 'is_mentor', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_per_page = 25
    inlines = [MentorInline]
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'
    
    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super().get_inline_instances(request, obj)
    
    actions = ['activate_users', 'deactivate_users']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')
    activate_users.short_description = 'Activate selected users'
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')
    deactivate_users.short_description = 'Deactivate selected users'

class AvailabilityInline(admin.TabularInline):
    model = Availability
    extra = 1
    fields = ('day_of_week', 'start_time', 'end_time', 'is_recurring')

@admin.register(Mentor)
class MentorAdmin(admin.ModelAdmin):
    list_display = ('user_link', 'title', 'company', 'is_available', 'session_count', 'upcoming_sessions_count')
    search_fields = ('user__username', 'title', 'company', 'user__email')
    list_filter = ('is_available', 'user__is_active')
    list_per_page = 25
    inlines = [AvailabilityInline]
    
    def user_link(self, obj):
        url = reverse('admin:core_user_change', args=[obj.user.id])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Username'
    user_link.admin_order_field = 'user__username'
    
    def session_count(self, obj):
        return obj.mentor_sessions.count()
    session_count.short_description = 'Total Sessions'
    
    def upcoming_sessions_count(self, obj):
        return obj.upcoming_sessions.count()
    upcoming_sessions_count.short_description = 'Upcoming'

class SessionStatusFilter(admin.SimpleListFilter):
    title = 'session status'
    parameter_name = 'status_time'

    def lookups(self, request, model_admin):
        return [
            ('upcoming', 'Upcoming Sessions'),
            ('past', 'Past Sessions'),
            ('today', 'Sessions Today'),
        ]

    def queryset(self, request, queryset):
        now = timezone.now()
        if self.value() == 'upcoming':
            return queryset.filter(scheduled_time__gt=now)
        if self.value() == 'past':
            return queryset.filter(scheduled_time__lt=now)
        if self.value() == 'today':
            today = now.date()
            return queryset.filter(scheduled_time__date=today)

@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('title', 'student_link', 'mentor_link', 'scheduled_time', 'duration_minutes', 'status_badge', 'created_at')
    list_filter = ('status', SessionStatusFilter, 'scheduled_time')
    search_fields = ('title', 'student__username', 'mentor__username', 'student__email', 'mentor__email')
    date_hierarchy = 'scheduled_time'
    list_per_page = 25
    actions = ['mark_as_completed', 'cancel_sessions']
    
    def student_link(self, obj):
        url = reverse('admin:core_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.username)
    student_link.short_description = 'Student'
    student_link.admin_order_field = 'student__username'
    
    def mentor_link(self, obj):
        url = reverse('admin:core_user_change', args=[obj.mentor.id])
        return format_html('<a href="{}">{}</a>', url, obj.mentor.username)
    mentor_link.short_description = 'Mentor'
    mentor_link.admin_order_field = 'mentor__username'
    
    def status_badge(self, obj):
        status_colors = {
            'requested': 'orange',
            'accepted': 'blue',
            'completed': 'green',
            'rejected': 'red',
            'cancelled': 'gray',
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 10px; font-size: 12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'status'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, f'{updated} sessions marked as completed.')
    mark_as_completed.short_description = 'Mark selected sessions as completed'
    
    def cancel_sessions(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} sessions have been cancelled.')
    cancel_sessions.short_description = 'Cancel selected sessions'

class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    readonly_fields = ('preview_image',)
    
    def preview_image(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 100px;" />', obj.image.url)
        return "No image"
    preview_image.short_description = 'Preview'

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'student_link', 'created_at', 'tech_stack_list')
    search_fields = ('title', 'description', 'student__username')
    list_filter = ('created_at',)
    inlines = [ProjectImageInline]
    list_per_page = 20
    
    def student_link(self, obj):
        url = reverse('admin:core_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.username)
    student_link.short_description = 'Student'
    
    def tech_stack_list(self, obj):
        return ", ".join(obj.get_tech_stack_list())
    tech_stack_list.short_description = 'Tech Stack'

@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('title', 'student_link', 'uploaded_at', 'is_primary')
    list_filter = ('is_primary', 'uploaded_at')
    search_fields = ('title', 'student__username')
    list_per_page = 20
    
    def student_link(self, obj):
        url = reverse('admin:core_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.username)
    student_link.short_description = 'Student'

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('mentor_link', 'student_link', 'created_at', 'short_content')
    search_fields = ('content', 'mentor__username', 'student__username')
    list_filter = ('created_at',)
    list_per_page = 20
    
    def mentor_link(self, obj):
        url = reverse('admin:core_user_change', args=[obj.mentor.id])
        return format_html('<a href="{}">{}</a>', url, obj.mentor.username)
    mentor_link.short_description = 'Mentor'
    
    def student_link(self, obj):
        url = reverse('admin:core_user_change', args=[obj.student.id])
        return format_html('<a href="{}">{}</a>', url, obj.student.username)
    student_link.short_description = 'Student'
    
    def short_content(self, obj):
        return f"{obj.content[:100]}..." if len(obj.content) > 100 else obj.content
    short_content.short_description = 'Content'

# Signal to create/delete mentor profile when user.is_mentor changes
@receiver(post_save, sender=User)
def update_mentor_profile(sender, instance, created, **kwargs):
    """Create or delete mentor profile when user.is_mentor changes."""
    if hasattr(instance, 'mentor_profile'):
        if not instance.is_mentor:
            # User is no longer a mentor, delete the profile
            instance.mentor_profile.delete()
    elif instance.is_mentor:
        # User is now a mentor, create a profile
        from .models import Mentor
        Mentor.objects.get_or_create(user=instance)
