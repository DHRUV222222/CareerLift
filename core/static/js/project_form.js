class ProjectForm {
    constructor() {
        this.fileInput = document.getElementById('file-upload');
        this.previewContainer = document.getElementById('preview-container');
        this.dropZone = document.getElementById('drop-zone');
        this.maxFiles = 5;
        this.maxFileSize = 5 * 1024 * 1024; // 5MB
        this.uploadedFiles = [];
        this.removedFiles = [];
        
        this.initialize();
    }
    
    initialize() {
        // Initialize file upload functionality
        if (this.fileInput) {
            this.setupFileInput();
            
            // Initialize drop zone if it exists
            if (this.dropZone) {
                this.setupDropZone();
            }
        }
        
        // Initialize tech stack tags input
        this.initializeTechStack();
    }
    
    setupFileInput() {
        // Clear existing event listeners by cloning the element
        const newFileInput = this.fileInput.cloneNode(true);
        this.fileInput.parentNode.replaceChild(newFileInput, this.fileInput);
        this.fileInput = newFileInput;
        
        // Add a single event listener
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e);
                // We don't reset the input value here to ensure files are submitted with the form
            }
        }, false);
    }
    
    setupDropZone() {
        const self = this;
        
        // Prevent default drag behaviors
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, this.preventDefaults, false);
        });

        // Highlight drop zone when item is dragged over it
        ['dragenter', 'dragover'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.add('border-primary-500', 'bg-blue-50');
            }, false);
        });

        // Unhighlight drop zone when item leaves
        ['dragleave', 'drop'].forEach(eventName => {
            this.dropZone.addEventListener(eventName, () => {
                this.dropZone.classList.remove('border-primary-500', 'bg-blue-50');
            }, false);
        });

        // Handle dropped files
        this.dropZone.addEventListener('drop', (e) => this.handleDrop(e), false);
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            this.handleFiles(files);
            // Clear the data transfer to prevent duplicate handling
            if (dt.items) {
                dt.items.clear();
            }
        }
    }
    
    handleFileSelect(e) {
        const files = e.target.files;
        this.handleFiles(files);
    }
    
    handleFiles(files) {
        const validFiles = [];
        const errors = [];
        const remainingSlots = this.maxFiles - this.uploadedFiles.length;

        // Check number of files
        if (files.length > remainingSlots) {
            errors.push(`You can only upload ${remainingSlots} more file(s). Maximum of ${this.maxFiles} files allowed.`);
            this.showError(errors.join('\n'));
            return;
        }

        // Process each file
        Array.from(files).forEach(file => {
            // Check file size
            if (file.size > this.maxFileSize) {
                errors.push(`File '${file.name}' is too large. Maximum size is 5MB.`);
                return;
            }

            // Check file type
            if (!file.type.match('image.*')) {
                errors.push(`File '${file.name}' is not an image.`);
                return;
            }

            // Add to valid files
            validFiles.push(file);
            this.uploadedFiles.push(file);
        });

        // Show errors if any
        if (errors.length > 0) {
            this.showError(errors.join('\n'));
        }

        // Add to preview
        this.addFilesToPreview(validFiles);
    }
        
        // Process valid files
        if (validFiles.length > 0) {
            this.processFiles(validFiles);
            this.updateFileInput();
        }
    }
    
    processFiles(files) {
        files.forEach(file => {
            this.createPreview(file);
        });
    }
    
    createPreview(file) {
        const reader = new FileReader();
        
        reader.onload = (e) => {
            const preview = document.createElement('div');
            preview.className = 'relative inline-block m-2 group';
            
            const img = document.createElement('img');
            img.src = e.target.result;
            img.className = 'h-24 w-24 object-cover rounded-lg';
            
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'absolute top-0 right-0 -mt-2 -mr-2 bg-red-500 text-white rounded-full p-1 opacity-0 group-hover:opacity-100 transition-opacity';
            removeBtn.innerHTML = '<svg class="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>';
            removeBtn.onclick = (e) => {
                e.preventDefault();
                e.stopPropagation();
                this.removeFile(file);
            };
            
            preview.appendChild(img);
            preview.appendChild(removeBtn);
            this.previewContainer.appendChild(preview);
        };
        
        reader.readAsDataURL(file);
    }
    
    removeFile(fileToRemove) {
        this.uploadedFiles = this.uploadedFiles.filter(file => file !== fileToRemove);
        this.updateFileInput();
        this.updatePreviews();
    }
    
    updateFileInput() {
        if (!this.fileInput) return;
        
        const dataTransfer = new DataTransfer();
        this.uploadedFiles.forEach(file => {
            dataTransfer.items.add(file);
        });
        
        this.fileInput.files = dataTransfer.files;
    }
    
    showError(message) {
        // Simple alert for now, can be replaced with a better UI
        alert(message);
    }
    
    initializeTechStack() {
        const techStackInput = document.getElementById('id_tech_stack');
        if (techStackInput && typeof $.fn.tagsinput !== 'undefined') {
            $(techStackInput).tagsinput({
                tagClass: 'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 mr-1 mb-1',
                trimValue: true,
                maxTags: 10,
                maxChars: 20,
                confirmKeys: [13, 188, 32], // Enter, comma, space
                cancelConfirmKeysOnEmpty: false
            });
        }
    }
}

// Initialize the form when the DOM is loaded
if (document.readyState === 'loading') {
    // Loading hasn't finished yet
    document.addEventListener('DOMContentLoaded', () => {
        window.projectForm = new ProjectForm();
    });
} else {
    // `DOMContentLoaded` has already fired
    window.projectForm = new ProjectForm();
}

// Global function to handle removal of existing images from the server
window.removeExistingImage = function(button) {
    if (confirm('Are you sure you want to remove this image? This action cannot be undone.')) {
        const imageId = button.getAttribute('data-image-id');
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Show loading state
        const originalHTML = button.innerHTML;
        button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        button.disabled = true;
        
        // Send AJAX request to delete the image
        fetch(`/projects/delete-image/${imageId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken,
                'X-Requested-With': 'XMLHttpRequest',
            },
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the image container from the UI
                const container = button.closest('.relative');
                if (container) {
                    container.remove();
                }
            } else {
                alert('Failed to delete the image. Please try again.');
                button.innerHTML = originalHTML;
                button.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the image.');
            button.innerHTML = originalHTML;
            button.disabled = false;
        });
    }
};
