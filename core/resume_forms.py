from django import forms
from django.core.exceptions import ValidationError
from .models import Resume

class ResumeForm(forms.ModelForm):
    class Meta:
        model = Resume
        fields = ['title', 'file', 'is_primary']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'E.g., Software Engineer Resume - 2025'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'})
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['file'].widget.attrs.update({
            'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100',
            'accept': '.pdf',
        })
        self.fields['title'].widget.attrs.update({
            'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
        })
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Limit file size to 5MB
            if file.size > 5 * 1024 * 1024:
                raise ValidationError('File size must be no more than 5MB.')
        return file
    
    def save(self, commit=True):
        resume = super().save(commit=False)
        if self.user:
            resume.student = self.user
        if commit:
            if resume.is_primary:
                # Ensure only one primary resume per user
                Resume.objects.filter(student=resume.student, is_primary=True).update(is_primary=False)
            resume.save()
        return resume
