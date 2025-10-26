// Global variables
let selectedFiles = [];
let allDriveFiles = [];

// Fetch .txt files from Google Drive
async function fetchDriveFiles() {
    try {
        const response = await fetch('/api/list-files');
        const result = await response.json();

        if (response.ok && result.success) {
            allDriveFiles = result.files;
            showFileSelectionModal();
        } else {
            alert('Error loading files from Google Drive: ' + (result.detail || 'Unknown error'));
        }
    } catch (error) {
        alert('Error loading files: ' + error.message);
    }
}

// Show custom file selection modal
function showFileSelectionModal() {
    if (allDriveFiles.length === 0) {
        alert('No .txt files found in your Google Drive. Please upload sermon transcript files first.');
        return;
    }

    const modal = document.createElement('div');
    modal.className = 'modal';
    modal.id = 'filePickerModal';

    const fileList = allDriveFiles.map((file, index) => `
        <div class="file-picker-item">
            <input type="checkbox" id="file_${index}" value="${file.id}"
                ${selectedFiles.some(f => f.id === file.id) ? 'checked' : ''}>
            <label for="file_${index}">${file.name}</label>
        </div>
    `).join('');

    modal.innerHTML = `
        <div class="modal-content file-picker">
            <h3>Select Sermon Transcript Files</h3>
            <p style="color: var(--text-secondary); margin-bottom: 1rem;">Select up to 8 .txt files (files will be ordered alphabetically)</p>
            <div class="file-picker-list">
                ${fileList}
            </div>
            <div class="modal-actions" style="margin-top: 1.5rem;">
                <button onclick="confirmFileSelection()" class="btn-primary">Confirm Selection</button>
                <button onclick="closeFilePickerModal()" class="btn-secondary">Cancel</button>
            </div>
        </div>
    `;

    document.body.appendChild(modal);
}

// Confirm file selection from modal
function confirmFileSelection() {
    const checkboxes = document.querySelectorAll('#filePickerModal input[type="checkbox"]:checked');

    if (checkboxes.length === 0) {
        alert('Please select at least one file.');
        return;
    }

    if (checkboxes.length > 8) {
        alert('Maximum 8 files allowed. Please deselect some files.');
        return;
    }

    selectedFiles = Array.from(checkboxes).map(cb => {
        const fileIndex = parseInt(cb.value) ?
            allDriveFiles.findIndex(f => f.id === cb.value) :
            parseInt(cb.id.replace('file_', ''));
        return allDriveFiles.find(f => f.id === cb.value) || allDriveFiles[fileIndex];
    });

    // Sort files alphabetically
    selectedFiles.sort((a, b) => a.name.localeCompare(b.name));

    updateSelectedFilesDisplay();
    updateFileIdsInput();
    toggleGenerateButton();
    closeFilePickerModal();
}

// Close file picker modal
function closeFilePickerModal() {
    const modal = document.getElementById('filePickerModal');
    if (modal) {
        modal.remove();
    }
}

// Update the display of selected files
function updateSelectedFilesDisplay() {
    const container = document.getElementById('selectedFiles');

    if (selectedFiles.length === 0) {
        container.innerHTML = '<p style="color: var(--text-secondary); font-size: 0.875rem; margin-top: 0.5rem;">No files selected</p>';
        return;
    }

    container.innerHTML = selectedFiles.map((file, index) => `
        <div class="file-item">
            <span>${file.name}</span>
            <button type="button" onclick="removeFile(${index})" title="Remove file">&times;</button>
        </div>
    `).join('');
}

// Update hidden input with file IDs
function updateFileIdsInput() {
    const fileIdsInput = document.getElementById('fileIds');
    fileIdsInput.value = selectedFiles.map(f => f.id).join(',');
}

// Remove a file from selection
function removeFile(index) {
    selectedFiles.splice(index, 1);
    updateSelectedFilesDisplay();
    updateFileIdsInput();
    toggleGenerateButton();
}

// Toggle generate button based on form validity
function toggleGenerateButton() {
    const generateBtn = document.getElementById('generateBtn');
    const seriesTitle = document.getElementById('seriesTitle').value.trim();
    const targetAudience = document.getElementById('targetAudience').value;
    const model = document.getElementById('model').value;
    const hasFiles = selectedFiles.length > 0;

    generateBtn.disabled = !(seriesTitle && targetAudience && model && hasFiles);
}

// Handle form submission
async function handleSubmit(event) {
    event.preventDefault();

    // Show loading overlay
    document.getElementById('loadingOverlay').classList.remove('hidden');

    const formData = new FormData(event.target);

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        // Hide loading overlay
        document.getElementById('loadingOverlay').classList.add('hidden');

        if (response.ok && result.success) {
            // Show success modal
            document.getElementById('driveLink').href = result.file_url;
            document.getElementById('successModal').classList.remove('hidden');
        } else {
            // Show error modal
            document.getElementById('errorMessage').textContent = result.detail || 'An unexpected error occurred.';
            document.getElementById('errorModal').classList.remove('hidden');
        }
    } catch (error) {
        console.error('Error:', error);
        document.getElementById('loadingOverlay').classList.add('hidden');
        document.getElementById('errorMessage').textContent = 'Network error: ' + error.message;
        document.getElementById('errorModal').classList.remove('hidden');
    }
}

// Close modal and reset form
function closeModal() {
    document.getElementById('successModal').classList.add('hidden');
    document.getElementById('errorModal').classList.add('hidden');

    // Reset form
    document.getElementById('generateForm').reset();
    selectedFiles = [];
    updateSelectedFilesDisplay();
    updateFileIdsInput();
    toggleGenerateButton();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // File picker button
    document.getElementById('pickerButton').addEventListener('click', fetchDriveFiles);

    // Form input listeners
    document.getElementById('seriesTitle').addEventListener('input', toggleGenerateButton);
    document.getElementById('targetAudience').addEventListener('change', toggleGenerateButton);
    document.getElementById('model').addEventListener('change', toggleGenerateButton);

    // Form submission
    document.getElementById('generateForm').addEventListener('submit', handleSubmit);

    // Initialize display
    updateSelectedFilesDisplay();
});
