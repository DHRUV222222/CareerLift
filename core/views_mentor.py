from django.views.generic import CreateView, ListView, DetailView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.core.exceptions import PermissionDenied

from .models import Mentor, Session, User
from .forms import SessionBookingForm
from .mixins import StudentRequiredMixin

class MentorListView(LoginRequiredMixin, ListView):
    model = Mentor
    template_name = 'mentor/list.html'
    context_object_name = 'mentors'
    
    def get_queryset(self):
        return Mentor.objects.filter(user__is_active=True)

class MentorDetailView(LoginRequiredMixin, DetailView):
    model = Mentor
    template_name = 'mentor/detail.html'
    context_object_name = 'mentor'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['available_slots'] = self.object.get_available_slots()
        return context

class BookMentorView(LoginRequiredMixin, StudentRequiredMixin, CreateView):
    model = Session
    form_class = SessionBookingForm
    template_name = 'mentor/book.html'
    
    def get_mentor(self):
        return get_object_or_404(Mentor, pk=self.kwargs['mentor_id'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mentor'] = self.get_mentor()
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['mentor'] = self.get_mentor()
        kwargs['student'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        session = form.save(commit=False)
        session.mentor = self.get_mentor()
        session.student = self.request.user
        session.status = 'requested'
        session.save()
        
        messages.success(
            self.request,
            'Your session request has been sent to the mentor. '
            'You will be notified once they respond.'
        )
        return redirect('core:student_dashboard')
    
    def form_invalid(self, form):
        messages.error(
            self.request,
            'There was an error with your booking. Please check the form and try again.'
        )
        return super().form_invalid(form)
