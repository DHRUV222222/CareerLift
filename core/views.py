from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import (
    LoginView as BaseLoginView,
    PasswordResetView as BasePasswordResetView,
    PasswordResetDoneView as BasePasswordResetDoneView,
    PasswordResetConfirmView as BasePasswordResetConfirmView,
    PasswordResetCompleteView as BasePasswordResetCompleteView,
)
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, UpdateView, TemplateView, FormView, ListView, DetailView


@login_required
def mentor_availability(request):
    """
    View for mentors to set their availability.
    """
    if not hasattr(request.user, 'mentor_profile'):
        messages.error(request, "You don't have permission to access this page.")
        return redirect('core:home')
        
    # TODO: Add availability form handling here
    
    context = {
        'page_title': 'Set Your Availability',
        'mentor': request.user.mentor_profile,
    }
    return render(request, 'mentor/availability.html', context)
from django.utils.decorators import method_decorator
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils import timezone
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from datetime import timedelta
import json

from .models import User, Mentor, Session, Project, Feedback
from .forms import (
    UserRegisterForm, 
    UserLoginForm, 
    UserUpdateForm, 
    MentorProfileForm
)
from .session_forms import SessionBookingForm

# Authentication Views
class RegisterView(CreateView):
    model = User
    form_class = UserRegisterForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('core:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(
            self.request, 
            'Your account has been created! You can now log in.'
        )
        return response

class LoginView(BaseLoginView):
    form_class = UserLoginForm
    template_name = 'registration/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        # Redirect to appropriate dashboard based on user type
        if self.request.user.is_mentor:
            return reverse_lazy('core:mentor_dashboard')
        return reverse_lazy('core:student_dashboard')

class PasswordResetView(BasePasswordResetView):
    email_template_name = 'registration/password_reset_email.html'
    template_name = 'registration/password_reset.html'
    success_url = reverse_lazy('core:password_reset_done')

class PasswordResetDoneView(BasePasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'

class PasswordResetConfirmView(BasePasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('core:password_reset_complete')

class PasswordResetCompleteView(BasePasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'

def custom_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('core:home')

# Profile Views
class ProfileView(LoginRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'mentor/profile.html'
    success_url = reverse_lazy('core:profile')
    
    def get_success_url(self):
        messages.success(self.request, 'Profile updated successfully!')
        return super().get_success_url()
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request.user, 'mentor') and self.request.user.mentor:
            context['mentor_form'] = MentorProfileForm(instance=self.request.user.mentor)
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)
    
    def form_valid(self, form):
        # Handle the user update form
        response = super().form_valid(form)
        
        # Handle the mentor form if the user has a mentor profile
        if hasattr(self.request.user, 'mentor') and self.request.user.mentor:
            mentor_form = MentorProfileForm(
                self.request.POST, 
                instance=self.request.user.mentor
            )
            if mentor_form.is_valid():
                mentor_form.save()
        
        messages.success(self.request, 'Your profile has been updated.')
        return response

# Main Views
class HomeView(TemplateView):
    template_name = 'home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            if self.request.user.is_mentor:
                context['dashboard_url'] = reverse_lazy('core:mentor_dashboard')
            else:
                context['dashboard_url'] = reverse_lazy('core:student_dashboard')
        return context

class StudentDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'student/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get user's resumes and projects
        resumes = user.resumes.all()
        projects = user.projects.all()
        
        # Get upcoming sessions (next 7 days)
        from django.utils import timezone
        from datetime import timedelta
        from .models import Session
        
        # Get all upcoming sessions (both requested and accepted)
        upcoming_sessions = Session.objects.filter(
            student=user,
            scheduled_time__gte=timezone.now(),
            status__in=['accepted', 'requested']
        ).order_by('scheduled_time')
        
        # Get only accepted sessions for the accepted sessions section
        accepted_sessions = Session.objects.filter(
            student=user,
            status='accepted',
            scheduled_time__gte=timezone.now()
        ).order_by('scheduled_time')
        
        # Get unique mentors from sessions
        mentor_ids = Session.objects.filter(
            student=user
        ).values_list('mentor', flat=True).distinct()
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        mentors = User.objects.filter(id__in=mentor_ids, is_mentor=True)
        
        # Count stats
        context.update({
            'resumes': resumes,
            'projects': projects,
            'upcoming_sessions': upcoming_sessions[:5],  # Show next 5 sessions
            'accepted_sessions': accepted_sessions[:5],   # Show next 5 accepted sessions
            'mentors_count': len(mentors),
            'projects_count': projects.count(),
            'sessions_count': user.student_sessions.count(),
            'resumes_count': resumes.count(),
            'mentors': mentors[:3],  # Show 3 recent mentors
            'recent_projects': projects.order_by('-created_at')[:3],
            'upcoming_sessions_count': upcoming_sessions.count(),
            'accepted_sessions_count': accepted_sessions.count(),
        })
        
        return context

class MentorDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'mentor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if not hasattr(self.request.user, 'mentor_profile'):
            return context
            
        mentor = self.request.user.mentor_profile
        now = timezone.now()
        
        # Get all sessions where the mentor is the current user
        mentor_sessions = mentor.mentor_sessions
        
        # Calculate total unique students
        total_students = mentor_sessions.values('student').distinct().count()
        
        # Get session statistics
        context.update({
            'mentor': mentor,
            'upcoming_sessions': mentor.upcoming_sessions[:5],
            'recent_sessions': mentor_sessions.order_by('-scheduled_time')[:5],
            'pending_requests': mentor.session_requests.count(),
            'total_students': total_students,
            'completed_sessions': mentor.completed_sessions.count(),
            'recent_activity': mentor_sessions.order_by('-updated_at')[:5],
            'now': now,
        })
        
        return context
