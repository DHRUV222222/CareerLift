from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.views.generic.edit import FormMixin
from django.forms import modelformset_factory
from django.db import transaction
from .models import Project, ProjectImage
from .project_forms import ProjectForm, ProjectImageForm

class ProjectListView(LoginRequiredMixin, ListView):
    """View for listing all projects of the logged-in student."""
    model = Project
    template_name = 'student/project/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        """Return only the projects for the currently logged-in user."""
        print(f"\n=== DEBUG: Fetching projects for user: {self.request.user.username} (ID: {self.request.user.id}) ===")
        queryset = Project.objects.filter(student=self.request.user).order_by('-created_at')
        print(f"=== DEBUG: Found {queryset.count()} projects ===")
        for project in queryset:
            print(f"- {project.title} (ID: {project.id})")
        return queryset

class ProjectCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new project with multiple images."""
    model = Project
    form_class = ProjectForm
    template_name = 'student/project/project_form.html'
    success_url = reverse_lazy('core:project_list')
    
    def get_form_kwargs(self):
        """Add request to form kwargs to access it in the form."""
        kwargs = super().get_form_kwargs()
        kwargs['request'] = self.request
        return kwargs
    
    def form_valid(self, form):
        try:
            with transaction.atomic():
                # Save the project first
                self.object = form.save(commit=False)
                self.object.student = self.request.user
                self.object.save()
                
                # Debug: Print FILES dictionary
                print("FILES:", self.request.FILES)
                
                # Handle file uploads
                if 'images' in self.request.FILES:
                    files = self.request.FILES.getlist('images')
                    print(f"Found {len(files)} files to upload")
                    
                    for i, image in enumerate(files, 1):
                        try:
                            print(f"Processing image {i}: {image.name} (size: {image.size} bytes, type: {image.content_type})")
                            
                            # Create the project image
                            project_image = ProjectImage(project=self.object, image=image)
                            project_image.save()
                            
                            print(f"Successfully saved image: {image.name}")
                            print(f"Image path: {project_image.image.path}")
                            print(f"Image URL: {project_image.image.url}")
                            
                        except Exception as e:
                            print(f"Error saving image {image.name}: {str(e)}")
                            messages.error(self.request, f'Error uploading {image.name}: {str(e)}')
                else:
                    print("No 'images' key in request.FILES")
                
                messages.success(self.request, 'Project created successfully!')
                return super().form_valid(form)
                
        except Exception as e:
            print(f"Unexpected error in form_valid: {str(e)}")
            messages.error(self.request, f'An error occurred while saving the project: {str(e)}')
            return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class ProjectUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating an existing project."""
    model = Project
    form_class = ProjectForm
    template_name = 'student/project/project_form.html'
    success_url = reverse_lazy('core:project_list')
    
    def test_func(self):
        project = self.get_object()
        return self.request.user == project.student
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Add the image field to the main form
        form.fields['image'] = ProjectImageForm().fields['image']
        return form
    
    def form_valid(self, form):
        with transaction.atomic():
            self.object = form.save()
            
            # Handle file uploads if any
            if 'image' in self.request.FILES:
                for file in self.request.FILES.getlist('image'):
                    if file:  # Ensure the file exists and has content
                        ProjectImage.objects.create(project=self.object, image=file)
        
        messages.success(self.request, 'Project updated successfully!')
        return super().form_valid(form)

class ProjectDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View for viewing project details."""
    model = Project
    template_name = 'student/project/project_detail.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the request to the context
        context['request'] = self.request
        # Add MEDIA_URL to the context
        context['MEDIA_URL'] = '/media/'
        # Prefetch related images to avoid N+1 query
        context['project'] = Project.objects.prefetch_related('images').get(pk=self.object.pk)
        return context
    
    def test_func(self):
        project = self.get_object()
        return self.request.user == project.student

class ProjectDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting a project."""
    model = Project
    template_name = 'student/project_confirm_delete.html'
    success_url = reverse_lazy('core:project_list')
    
    def test_func(self):
        project = self.get_object()
        return self.request.user == project.student
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, 'Project deleted successfully!')
        return super().delete(request, *args, **kwargs)

class ProjectImageDeleteView(LoginRequiredMixin, UserPassesTestMixin, View):
    """View for deleting a project image."""
    
    def test_func(self):
        image = get_object_or_404(ProjectImage, pk=self.kwargs['pk'])
        return self.request.user == image.project.student
    
    def post(self, request, *args, **kwargs):
        image = get_object_or_404(ProjectImage, pk=self.kwargs['pk'])
        project = image.project
        image.delete()
        messages.success(request, 'Image deleted successfully!')
        return redirect('core:project_update', pk=project.pk)
