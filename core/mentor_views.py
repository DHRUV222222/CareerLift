from django.views.generic import ListView, UpdateView, TemplateView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse_lazy
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone

from .models import Session, Mentor, Availability
from .forms import MentorProfileForm, AvailabilityFormSet, SessionForm

class MentorRequiredMixin(LoginRequiredMixin):
    """Verify that the current user is a mentor."""
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to access the mentor dashboard.")
            return redirect('core:login')
            
        # Check if user is marked as a mentor
        if not request.user.is_mentor:
            messages.error(request, 
                "You don't have mentor privileges. "
                "Please contact support to be set up as a mentor."
            )
            return redirect('core:home')
            
        # Get or create mentor profile safely
        from django.db import IntegrityError
        from .models import Mentor
        
        # First try to get the mentor profile
        if not hasattr(request.user, 'mentor_profile'):
            try:
                # Try to create a mentor profile if it doesn't exist
                Mentor.objects.get_or_create(user=request.user)
                messages.info(request, "Your mentor profile has been created.")
            except IntegrityError:
                # In case of race condition, just get the existing profile
                pass
                
        return super().dispatch(request, *args, **kwargs)

class MentorSessionRequestsView(MentorRequiredMixin, ListView):
    """View for mentors to see their pending session requests."""
    model = Session
    template_name = 'mentor/session_requests.html'
    context_object_name = 'session_requests'
    
    def get_queryset(self):
        # Ensure mentor profile exists
        mentor_profile = getattr(self.request.user, 'mentor_profile', None)
        if not mentor_profile:
            # If for some reason the profile doesn't exist, create it
            mentor_profile, created = Mentor.objects.get_or_create(user=self.request.user)
            if created:
                messages.info(self.request, "Your mentor profile has been created.")
        return mentor_profile.session_requests.order_by('scheduled_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor_profile = getattr(self.request.user, 'mentor_profile', None)
        if not mentor_profile:
            # If for some reason the profile doesn't exist, create it
            mentor_profile, created = Mentor.objects.get_or_create(user=self.request.user)
            if created:
                messages.info(self.request, "Your mentor profile has been created.")
        
        context['upcoming_sessions'] = mentor_profile.upcoming_sessions
        context['completed_sessions'] = mentor_profile.completed_sessions
        return context

class UpdateSessionStatusView(MentorRequiredMixin, UpdateView):
    """View for mentors to accept or reject session requests."""
    model = Session
    fields = []  # We'll handle the status in the form_valid method
    http_method_names = ['post']  # Only allow POST requests
    
    def get_queryset(self):
        # Ensure mentor profile exists
        mentor_profile = getattr(self.request.user, 'mentor_profile', None)
        if not mentor_profile:
            # If for some reason the profile doesn't exist, create it
            mentor_profile, created = Mentor.objects.get_or_create(user=self.request.user)
            if created:
                messages.info(self.request, "Your mentor profile has been created.")
        return Session.objects.filter(mentor=self.request.user)
    
    def post(self, request, *args, **kwargs):
        session = self.get_object()
        action = request.POST.get('action')
        
        if action == 'accept':
            session.status = 'accepted'
            # Ensure the mentor field is set to the current user
            session.mentor = request.user
            message = 'Session request has been accepted.'
        elif action == 'reject':
            session.status = 'rejected'
            message = 'Session request has been rejected.'
        else:
            messages.error(request, 'Invalid action.')
            return redirect('core:mentor_session_requests')
        
        session.save()
        messages.success(request, message)
        return redirect('core:mentor_session_requests')

class MentorUpcomingSessionsView(MentorRequiredMixin, ListView):
    """View for mentors to see their upcoming sessions."""
    model = Session
    template_name = 'mentor/upcoming_sessions.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        # Ensure mentor profile exists
        mentor_profile = getattr(self.request.user, 'mentor_profile', None)
        if not mentor_profile:
            # If for some reason the profile doesn't exist, create it
            mentor_profile, created = Mentor.objects.get_or_create(user=self.request.user)
            if created:
                messages.info(self.request, "Your mentor profile has been created.")
        return mentor_profile.upcoming_sessions

class MentorCompletedSessionsView(MentorRequiredMixin, ListView):
    """View for mentors to see their completed sessions."""
    model = Session
    template_name = 'mentor/completed_sessions.html'
    context_object_name = 'sessions'
    
    def get_queryset(self):
        # Ensure mentor profile exists
        mentor_profile = getattr(self.request.user, 'mentor_profile', None)
        if not mentor_profile:
            # If for some reason the profile doesn't exist, create it
            mentor_profile, created = Mentor.objects.get_or_create(user=self.request.user)
            if created:
                messages.info(self.request, "Your mentor profile has been created.")
        return mentor_profile.completed_sessions


class MentorSessionsView(MentorRequiredMixin, ListView):
    """View for mentors to manage their sessions."""
    model = Session
    template_name = 'mentor/sessions.html'
    context_object_name = 'sessions'
    paginate_by = 10

    def get_queryset(self):
        return Session.objects.filter(
            mentor=self.request.user,
            status__in=['requested', 'accepted', 'scheduled']
        ).order_by('scheduled_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'sessions'
        return context


class SessionUpdateView(MentorRequiredMixin, UpdateView):
    """View for updating session details."""
    model = Session
    form_class = SessionForm
    template_name = 'mentor/session_form.html'
    
    def get_queryset(self):
        return Session.objects.filter(mentor=self.request.user)
    
    def get_success_url(self):
        messages.success(self.request, 'Session updated successfully.')
        return reverse_lazy('core:mentor_sessions')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_tab'] = 'sessions'
        return context


class SessionDeleteView(MentorRequiredMixin, DeleteView):
    """View for deleting a session."""
    model = Session
    template_name = 'mentor/session_confirm_delete.html'
    success_url = reverse_lazy('core:mentor_sessions')
    
    def get_queryset(self):
        return Session.objects.filter(mentor=self.request.user)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Session has been cancelled.')
        return super().delete(request, *args, **kwargs)


class MentorAvailabilityView(MentorRequiredMixin, TemplateView):
    """View for mentors to manage their weekly availability."""
    template_name = 'mentor/availability.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor = self.request.user.mentor_profile
        
        form = MentorProfileForm(
            instance=mentor,
            prefix='profile',
            initial={'is_available': mentor.is_available}
        )
        formset = AvailabilityFormSet(
            instance=mentor,
            prefix='availability'
        )
        
        context.update({
            'form': form,
            'formset': formset,
            'mentor': mentor,
            'days_of_week': dict(Availability.DAYS_OF_WEEK),
        })
        return context
    
    def post(self, request, *args, **kwargs):
        mentor = request.user.mentor_profile
        form = MentorProfileForm(
            request.POST, 
            instance=mentor,
            prefix='profile'
        )
        formset = AvailabilityFormSet(
            request.POST,
            instance=mentor,
            prefix='availability'
        )
        
        if form.is_valid() and formset.is_valid():
            form.save()
            instances = formset.save(commit=False)
            
            # Handle deleted forms
            for obj in formset.deleted_objects:
                obj.delete()
                
            # Save new and updated instances
            for instance in instances:
                instance.mentor = mentor
                instance.save()
                
            messages.success(request, 'Your availability has been updated successfully.')
            return redirect('core:mentor_availability')
        
        # If form is invalid, render the form with errors
        context = self.get_context_data(**kwargs)
        context['form'] = form
        context['formset'] = formset
        return self.render_to_response(context)
