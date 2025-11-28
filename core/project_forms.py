from django import forms
from django.core.exceptions import ValidationError
from .models import Project, ProjectImage
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _

class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True
    input_type = 'file'
    template_name = 'widgets/multiple_input.html'

    def __init__(self, attrs=None):
        default_attrs = {
            'multiple': True,
            'accept': 'image/*',
            'class': 'hidden',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return [single_file_clean(data, initial)]

class ProjectForm(forms.ModelForm):
    """Form for creating and updating projects with multiple image uploads."""
    images = MultipleFileField(
        required=False,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif'],
                message=_('Only JPG, JPEG, PNG, and GIF images are allowed.')
            )
        ],
        help_text=_('Upload project screenshots (max 5MB each, max 5 files)')
    )
    tech_stack = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'data-role': 'tagsinput'}),
        help_text=_('Add technologies separated by commas (e.g., Python, Django, React)')
    )
    
    class Meta:
        model = Project
        fields = ['title', 'description', 'tech_stack', 'images']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4, 'class': 'form-textarea'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['tech_stack'].initial = self.instance.tech_stack
        super().__init__(*args, **kwargs)
        self.fields['images'].widget.attrs.update({
            'id': 'file-upload',
            'x-ref': 'fileInput',
            '@change': 'handleFileSelect($event)'
        })
    
    def clean_images(self):
        """Clean and validate the uploaded images."""
        images = self.files.getlist('images')
        if len(images) > 5:
            raise ValidationError(_('You can upload a maximum of 5 images.'))
        for image in images:
            if image.size > 5 * 1024 * 1024:  # 5MB
                raise ValidationError(_(f'File {image.name} is too large. Maximum size is 5MB.'))
        return images
    
    class Meta:
        model = Project
        fields = ['title', 'description', 'tech_stack']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'Project Title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'rows': 4,
                'placeholder': 'Project description, features, and technologies used...',
            }),
            'tech_stack': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                'placeholder': 'e.g., Python, Django, React, PostgreSQL',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        # Make fields required
        self.fields['title'].required = True
        self.fields['description'].required = True
        self.fields['tech_stack'].required = True
    
    def clean_image(self):
        """Validate uploaded images."""
        images = self.files.getlist('image')
        
        # Check if any images were uploaded
        if not images or len(images) == 0:
            return None
            
        # Check number of images (max 5)
        if len(images) > 5:
            raise forms.ValidationError('You can upload a maximum of 5 images.')
            
        # Check each image size (max 5MB)
        for img in images:
            if img.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError(f'Image {img.name} is too large. Maximum size is 5MB.')
                
        return images

class ProjectImageForm(forms.ModelForm):
    """Form for uploading project images."""
    image = MultipleFileField(
        required=False,
        help_text=_('Select one or more images to upload (max 5MB each, max 5 files).'),
        validators=[
            FileExtensionValidator(
                allowed_extensions=['jpg', 'jpeg', 'png', 'gif'],
                message='Only JPG, JPEG, PNG, and GIF images are allowed.'
            )
        ]
    )

    class Meta:
        model = ProjectImage
        fields = ['image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.update({
            'id': 'file-upload',
            'x-ref': 'fileInput',
            '@change': 'handleFileSelect($event)'
        })

    def clean_image(self):
        images = self.cleaned_data.get('image', [])
        for img in images:
            if img.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError(f"Image {img.name} is too large. Maximum size is 5MB.")
        return images
