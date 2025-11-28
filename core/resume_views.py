from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.http import FileResponse, Http404
from django.conf import settings
import os
from .models import Resume
from .resume_forms import ResumeForm

class ResumeListView(LoginRequiredMixin, ListView):
    model = Resume
    template_name = 'student/resume_list.html'
    context_object_name = 'resumes'
    
    def get_queryset(self):
        return Resume.objects.filter(student=self.request.user).order_by('-is_primary', '-uploaded_at')

class ResumeCreateView(LoginRequiredMixin, CreateView):
    model = Resume
    form_class = ResumeForm
    template_name = 'student/resume_form.html'
    success_url = reverse_lazy('core:resume_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.student = self.request.user
        messages.success(self.request, 'Resume uploaded successfully!')
        return super().form_valid(form)

class ResumeUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Resume
    form_class = ResumeForm
    template_name = 'student/resume_form.html'
    success_url = reverse_lazy('core:resume_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs
    
    def test_func(self):
        resume = self.get_object()
        return self.request.user == resume.student
    
    def form_valid(self, form):
        messages.success(self.request, 'Resume updated successfully!')
        return super().form_valid(form)

class ResumeDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Resume
    success_url = reverse_lazy('core:resume_list')
    template_name = 'student/resume_confirm_delete.html'
    
    def test_func(self):
        resume = self.get_object()
        return self.request.user == resume.student
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Resume deleted successfully!')
        return super().delete(request, *args, **kwargs)

class SetPrimaryResumeView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        resume = get_object_or_404(Resume, pk=kwargs['pk'], student=request.user)
        Resume.objects.filter(student=request.user, is_primary=True).update(is_primary=False)
        resume.is_primary = True
        resume.save()
        messages.success(request, 'Primary resume updated successfully!')
        return redirect('core:resume_list')


class ResumeDownloadView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View for downloading a resume file."""
    
    def test_func(self):
        """Ensure the user can only download their own resumes."""
        resume = get_object_or_404(Resume, pk=self.kwargs['pk'])
        return self.request.user == resume.student
    
    def get(self, request, *args, **kwargs):
        """Handle GET request to download the resume file."""
        resume = get_object_or_404(Resume, pk=kwargs['pk'])
        
        # Get the file path
        file_path = os.path.join(settings.MEDIA_ROOT, str(resume.file))
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise Http404("The requested file does not exist.")
        
        # Get the file extension and content type
        _, file_extension = os.path.splitext(file_path)
        content_type = 'application/pdf'  # Default to PDF
        
        # Set appropriate content type based on file extension
        if file_extension.lower() == '.docx':
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif file_extension.lower() == '.doc':
            content_type = 'application/msword'
        elif file_extension.lower() == '.txt':
            content_type = 'text/plain'
        
        # Create a file response with the appropriate headers
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
        return response
