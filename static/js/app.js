// Global variables
let selectedFiles = [];
let pickerApiLoaded = false;

// Load Google Picker API
function loadPicker() {
    gapi.load('picker', {'callback': onPickerApiLoad});
}

function onPickerApiLoad() {
    pickerApiLoaded = true;
}

// Get OAuth access token from backend
async function getAccessToken() {
    try {
        const response = await fetch('/api/access-token');
        const data = await response.json();
        return data.access_token;
    } catch (error) {
        console.error('Error getting access token:', error);
        alert('Failed to get access token. Please try logging in again.');
        return null;
    }
}

// Create and show Google Drive Picker
async function createPicker() {
    if (!pickerApiLoaded) {
        alert('Google Picker is still loading. Please try again in a moment.');
        return;
    }

    // Get access token from backend
    const token = await getAccessToken();
    if (!token) {
        return;
    }

    // Create a view that shows folders and allows navigation
    const docsView = new google.picker.DocsView(google.picker.ViewId.FOLDERS)
        .setIncludeFolders(true)
        .setSelectFolderEnabled(false)  // Don't allow selecting folders, only files
        .setMode(google.picker.DocsViewMode.LIST);

    const picker = new google.picker.PickerBuilder()
        .addView(docsView)
        .setOAuthToken(token)
        .setDeveloperKey(GOOGLE_API_KEY)
        .setCallback(pickerCallback)
        .enableFeature(google.picker.Feature.MULTISELECT_ENABLED)
        .setTitle('Select Sermon Transcript Files')
        .build();
    picker.setVisible(true);
}

// Handle file selection from Google Picker
function pickerCallback(data) {
    if (data.action === google.picker.Action.PICKED) {
        selectedFiles = data.docs.map(doc => ({
            id: doc.id,
            name: doc.name
        }));

        // Sort files alphabetically (handles "## 01, 02..." pattern)
        selectedFiles.sort((a, b) => a.name.localeCompare(b.name));

        // Limit to 8 files
        if (selectedFiles.length > 8) {
            selectedFiles = selectedFiles.slice(0, 8);
            alert('Maximum 8 files allowed. Only the first 8 alphabetically have been selected.');
        }

        updateSelectedFilesDisplay();
        updateFileIdsInput();
        toggleGenerateButton();
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
    // Load Google Picker API
    loadPicker();

    // File picker button
    document.getElementById('pickerButton').addEventListener('click', createPicker);

    // Form input listeners
    document.getElementById('seriesTitle').addEventListener('input', toggleGenerateButton);
    document.getElementById('targetAudience').addEventListener('change', toggleGenerateButton);
    document.getElementById('model').addEventListener('change', toggleGenerateButton);

    // Form submission
    document.getElementById('generateForm').addEventListener('submit', handleSubmit);

    // Initialize display
    updateSelectedFilesDisplay();
});
