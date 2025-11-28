from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.views.generic import ListView, CreateView, DetailView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q

from .models import User, Session
from .session_forms import SessionBookingForm


class MentorListView(LoginRequiredMixin, ListView):
    """View to list all available mentors."""
    model = User
    template_name = 'student/mentor_list.html'
    context_object_name = 'mentors'
    paginate_by = 10
    
    def get_queryset(self):
        # Get all users who are mentors and have a mentor profile
        return User.objects.filter(
            is_mentor=True,
            mentor_profile__isnull=False
        ).select_related('mentor_profile')
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the current path without query parameters to the context
        context['current_path'] = self.request.path
        return context


class BookSessionView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    """View for booking a session with a mentor."""
    model = Session
    form_class = SessionBookingForm
    template_name = 'student/book_session.html'
    
    def test_func(self):
        # Only students can book sessions
        return self.request.user.is_student
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        mentor = get_object_or_404(User, id=self.kwargs['mentor_id'], is_mentor=True)
        context['mentor'] = mentor
        return context
    
    def form_valid(self, form):
        mentor = get_object_or_404(User, id=self.kwargs['mentor_id'], is_mentor=True)
        session = form.save(commit=False)
        session.student = self.request.user
        session.mentor = mentor
        session.status = 'requested'
        session.save()
        messages.success(self.request, 'Session request sent successfully!')
        return redirect('core:student_dashboard')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['mentor_id'] = self.kwargs['mentor_id']
        return kwargs
        
    def get_success_url(self):
        return reverse('core:student_dashboard')


class SessionDetailView(LoginRequiredMixin, DetailView):
    """View to see details of a specific session."""
    model = Session
    template_name = 'student/session_detail.html'
    context_object_name = 'session'
    
    def get_queryset(self):
        # Users can only see their own sessions
        return Session.objects.filter(
            Q(student=self.request.user) | 
            Q(mentor=self.request.user)
        )


@method_decorator(login_required, name='dispatch')
class SessionUpdateView(UpdateView):
    """View to update a session (e.g., reschedule or cancel)."""
    model = Session
    form_class = SessionBookingForm
    template_name = 'student/update_session.html'
    
    def get_success_url(self):
        messages.success(self.request, 'Session updated successfully!')
        return reverse('core:session_detail', kwargs={'pk': self.object.pk})
    
    def get_queryset(self):
        # Users can only update their own sessions
        return Session.objects.filter(
            Q(student=self.request.user) | 
            Q(mentor=self.request.user)
        )
    
    def form_valid(self, form):
        # Only allow certain status changes based on user role
        session = self.get_object()
        if 'status' in form.changed_data:
            new_status = form.cleaned_data['status']
            if (self.request.user == session.mentor and 
                session.status == 'requested' and 
                new_status in ['accepted', 'rejected']):
                # Mentor can accept or reject requested sessions
                pass
            elif (self.request.user == session.student and 
                  new_status == 'cancelled' and 
                  session.status in ['requested', 'accepted']):
                # Student can cancel requested or accepted sessions
                pass
            else:
                form.add_error('status', 'Invalid status change')
                return self.form_invalid(form)
        return super().form_valid(form)


@require_http_methods(['POST'])
@login_required
def cancel_session(request, pk):
    """View to cancel a session."""
    session = get_object_or_404(Session, pk=pk)
    
    # Check permissions
    if request.user not in [session.student, session.mentor]:
        return HttpResponseForbidden()
    
    # Only allow cancellation of pending or accepted sessions
    if session.status in ['requested', 'accepted']:
        session.status = 'cancelled'
        session.save()
        messages.success(request, 'Session has been cancelled.')
    else:
        messages.error(request, 'Cannot cancel a session that is already completed or cancelled.')
    
    return redirect('core:student_dashboard' if request.user.is_student else 'core:mentor_dashboard')
