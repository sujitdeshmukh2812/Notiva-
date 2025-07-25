// Notiva Admin Dashboard JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Confirmation dialogs for delete actions
    const deleteButtons = document.querySelectorAll('[data-confirm]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            const message = this.getAttribute('data-confirm');
            if (!confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // Academic structure management
    initializeAcademicManagement();
    
    // Ad management
    initializeAdManagement();
    
    // Material management
    initializeMaterialManagement();
});

function loadYears(courseId, yearSelect, callback) {
    fetch(`/get_years/${courseId}`)
        .then(response => response.json())
        .then(years => {
            yearSelect.innerHTML = '<option value="">Select Year</option>';
            if (years.length === 0) {
                yearSelect.disabled = true;
                if (yearSelect.id === 'semesterYear') {
                    document.getElementById('semesterYearMsg').textContent = 'No years found for this course. Please add a year first!';
                    document.getElementById('semesterYearMsg').style.display = 'block';
                }
                if (yearSelect.id === 'subjectYear') {
                    document.getElementById('subjectYearMsg').textContent = 'No years found for this course. Please add a year first!';
                    document.getElementById('subjectYearMsg').style.display = 'block';
                }
                if (callback) callback(false);
            } else {
                years.forEach(year => {
                    yearSelect.innerHTML += `<option value="${year.id}">${year.name}</option>`;
                });
                yearSelect.disabled = false;
                if (yearSelect.id === 'semesterYear') {
                    document.getElementById('semesterYearMsg').style.display = 'none';
                }
                if (yearSelect.id === 'subjectYear') {
                    document.getElementById('subjectYearMsg').style.display = 'none';
                }
                if (callback) callback(true);
            }
        })
        .catch(error => {
            console.error('Error loading years:', error);
            showNotification('Error loading years', 'danger');
            if (callback) callback(false);
        });
}

function loadSemesters(yearId, semesterSelect, callback) {
    fetch(`/get_semesters/${yearId}`)
        .then(response => response.json())
        .then(semesters => {
            semesterSelect.innerHTML = '<option value="">Select Semester</option>';
            if (semesters.length === 0) {
                semesterSelect.disabled = true;
                if (semesterSelect.id === 'subjectSemester') {
                    document.getElementById('subjectSemesterMsg').textContent = 'No semesters found for this year. Please add a semester first!';
                    document.getElementById('subjectSemesterMsg').style.display = 'block';
                }
                if (callback) callback(false);
            } else {
                semesters.forEach(semester => {
                    semesterSelect.innerHTML += `<option value="${semester.id}">${semester.name}</option>`;
                });
                semesterSelect.disabled = false;
                if (semesterSelect.id === 'subjectSemester') {
                    document.getElementById('subjectSemesterMsg').style.display = 'none';
                }
                if (callback) callback(true);
            }
        })
        .catch(error => {
            console.error('Error loading semesters:', error);
            showNotification('Error loading semesters', 'danger');
            if (callback) callback(false);
        });
}

function initializeAdManagement() {
    // Ad form validation
    const adForm = document.getElementById('adForm');
    if (adForm) {
        adForm.addEventListener('submit', function(e) {
            const title = this.querySelector('[name="title"]').value.trim();
            const content = this.querySelector('[name="content"]').value.trim();
            
            if (!title || !content) {
                e.preventDefault();
                showNotification('Title and content are required', 'danger');
            }
        });
    }

    // Ad toggle handlers
    const toggleButtons = document.querySelectorAll('.toggle-ad-btn');
    toggleButtons.forEach(button => {
        button.addEventListener('click', function() {
            const adId = this.getAttribute('data-ad-id');
            toggleAd(adId, this);
        });
    });
}

function toggleAd(adId, button) {
    const currentText = button.textContent.trim();
    const isActive = currentText === 'Deactivate';
    
    fetch(`/admin/toggle_ad/${adId}`, {
        method: 'GET'
    })
    .then(response => {
        if (response.ok) {
            // Update button text and class
            if (isActive) {
                button.textContent = 'Activate';
                button.classList.remove('btn-warning');
                button.classList.add('btn-success');
            } else {
                button.textContent = 'Deactivate';
                button.classList.remove('btn-success');
                button.classList.add('btn-warning');
            }
            
            // Update status badge
            const statusBadge = button.closest('tr').querySelector('.status-badge');
            if (statusBadge) {
                if (isActive) {
                    statusBadge.textContent = 'Inactive';
                    statusBadge.classList.remove('bg-success');
                    statusBadge.classList.add('bg-secondary');
                } else {
                    statusBadge.textContent = 'Active';
                    statusBadge.classList.remove('bg-secondary');
                    statusBadge.classList.add('bg-success');
                }
            }
            
            showNotification('Ad status updated successfully', 'success');
        } else {
            showNotification('Error updating ad status', 'danger');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Error updating ad status', 'danger');
    });
}

function initializeMaterialManagement() {
    // Status filter handler
    const statusFilter = document.getElementById('statusFilter');
    if (statusFilter) {
        statusFilter.addEventListener('change', function() {
            const status = this.value;
            window.location.href = `/admin/notes?status=${status}`;
        });
    }

    // Bulk actions
    const selectAllCheckbox = document.getElementById('selectAll');
    const itemCheckboxes = document.querySelectorAll('.item-checkbox');
    const bulkActionBtn = document.getElementById('bulkActionBtn');

    if (selectAllCheckbox) {
        selectAllCheckbox.addEventListener('change', function() {
            itemCheckboxes.forEach(checkbox => {
                checkbox.checked = this.checked;
            });
            updateBulkActionBtn();
        });
    }

    itemCheckboxes.forEach(checkbox => {
        checkbox.addEventListener('change', updateBulkActionBtn);
    });

    function updateBulkActionBtn() {
        const selectedCount = document.querySelectorAll('.item-checkbox:checked').length;
        if (bulkActionBtn) {
            bulkActionBtn.style.display = selectedCount > 0 ? 'block' : 'none';
            bulkActionBtn.textContent = `Bulk Actions (${selectedCount} selected)`;
        }
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 1050; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    document.body.appendChild(notification);
    
    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 5000);
}

// Statistics animation
function animateStats() {
    const statNumbers = document.querySelectorAll('.stats-number');
    
    statNumbers.forEach(stat => {
        const target = parseInt(stat.textContent);
        const increment = target / 50;
        let current = 0;
        
        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                stat.textContent = target;
                clearInterval(timer);
            } else {
                stat.textContent = Math.floor(current);
            }
        }, 30);
    });
}

// Initialize stats animation when page loads
window.addEventListener('load', animateStats);

// Search functionality
function initializeSearch() {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.toLowerCase();
            const rows = document.querySelectorAll('tbody tr');
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        });
    }
}

// Initialize search
initializeSearch();

// Export functionality
function exportData(format) {
    const form = document.createElement('form');
    form.method = 'POST';
    form.action = '/admin/export';
    
    const formatInput = document.createElement('input');
    formatInput.type = 'hidden';
    formatInput.name = 'format';
    formatInput.value = format;
    
    form.appendChild(formatInput);
    document.body.appendChild(form);
    form.submit();
    document.body.removeChild(form);
}

// Make functions globally available
window.exportData = exportData;
window.showNotification = showNotification;

function initializeAcademicManagement() {
    // Course selection change handler for Year Modal
    const yearCourseSelect = document.getElementById('yearCourse');
    const yearSaveBtn = document.getElementById('yearSaveText')?.closest('button');
    if (yearCourseSelect && yearSaveBtn) {
        yearCourseSelect.addEventListener('change', function() {
            if (this.value) {
                document.getElementById('yearName').disabled = false;
                yearSaveBtn.disabled = false;
            } else {
                document.getElementById('yearName').disabled = true;
                yearSaveBtn.disabled = true;
            }
        });
    }

    // Semester Modal: Enable year dropdown and save button only if course and year are selected
    const semesterCourseSelect = document.getElementById('semesterCourse');
    const semesterYearSelect = document.getElementById('semesterYear');
    const semesterNameInput = document.getElementById('semesterName');
    const semesterSaveBtn = document.getElementById('semesterSaveBtn');
    
    if (semesterCourseSelect && semesterYearSelect && semesterNameInput && semesterSaveBtn) {
        // Enable/disable year dropdown based on course selection
        semesterCourseSelect.addEventListener('change', function() {
            const courseId = this.value;
            semesterYearSelect.innerHTML = '<option value="">Select Year</option>';
            semesterYearSelect.disabled = !courseId;
            semesterNameInput.disabled = true;
            semesterSaveBtn.disabled = true;
            
            if (courseId) {
                loadYears(courseId, semesterYearSelect, (hasYears) => {
                    if (!hasYears) {
                        semesterNameInput.disabled = true;
                        semesterSaveBtn.disabled = true;
                    }
                });
            }
        });

        // Enable/disable semester name input and save button based on year selection
        semesterYearSelect.addEventListener('change', function() {
            const yearId = this.value;
            semesterNameInput.disabled = !yearId;
            semesterSaveBtn.disabled = !yearId;
        });
    }

    // Subject Modal: Enable year and semester dropdowns and save button only if parents are selected
    const subjectCourseSelect = document.getElementById('subjectCourse');
    const subjectYearSelect = document.getElementById('subjectYear');
    const subjectSemesterSelect = document.getElementById('subjectSemester');
    const subjectNameInput = document.getElementById('subjectName');
    const subjectSaveBtn = document.getElementById('subjectSaveBtn');
    
    if (subjectCourseSelect && subjectYearSelect && subjectSemesterSelect && subjectSaveBtn) {
        // Enable/disable year dropdown based on course selection
        subjectCourseSelect.addEventListener('change', function() {
            const courseId = this.value;
            subjectYearSelect.innerHTML = '<option value="">Select Year</option>';
            subjectSemesterSelect.innerHTML = '<option value="">Select Semester</option>';
            subjectYearSelect.disabled = !courseId;
            subjectSemesterSelect.disabled = true;
            subjectNameInput.disabled = true;
            subjectSaveBtn.disabled = true;
            
            if (courseId) {
                fetch(`/get_years/${courseId}`)
                    .then(response => response.json())
                    .then(years => {
                        if (years.length === 0) {
                            document.getElementById('subjectYearMsg').textContent = 'No years found for this course. Add a year first!';
                            document.getElementById('subjectYearMsg').style.display = 'block';
                        } else {
                            years.forEach(year => {
                                subjectYearSelect.innerHTML += `<option value="${year.id}">${year.name}</option>`;
                            });
                            document.getElementById('subjectYearMsg').style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Error loading years:', error);
                        showNotification('Error loading years', 'danger');
                    });
            }
        });

        // Enable/disable semester dropdown based on year selection
        subjectYearSelect.addEventListener('change', function() {
            const yearId = this.value;
            subjectSemesterSelect.innerHTML = '<option value="">Select Semester</option>';
            subjectSemesterSelect.disabled = !yearId;
            subjectNameInput.disabled = true;
            subjectSaveBtn.disabled = true;
            
            if (yearId) {
                fetch(`/get_semesters/${yearId}`)
                    .then(response => response.json())
                    .then(semesters => {
                        if (semesters.length === 0) {
                            document.getElementById('subjectSemesterMsg').textContent = 'No semesters found for this year. Add a semester first!';
                            document.getElementById('subjectSemesterMsg').style.display = 'block';
                        } else {
                            semesters.forEach(semester => {
                                subjectSemesterSelect.innerHTML += `<option value="${semester.id}">${semester.name}</option>`;
                            });
                            document.getElementById('subjectSemesterMsg').style.display = 'none';
                        }
                    })
                    .catch(error => {
                        console.error('Error loading semesters:', error);
                        showNotification('Error loading semesters', 'danger');
                    });
            }
        });

        // Enable/disable subject name input based on semester selection
        subjectSemesterSelect.addEventListener('change', function() {
            const semesterId = this.value;
            subjectNameInput.disabled = !semesterId;
            subjectSaveBtn.disabled = !semesterId;
            
            if (semesterId) {
                document.getElementById('subjectSemesterMsg').style.display = 'none';
            } else {
                document.getElementById('subjectSemesterMsg').textContent = 'Select a semester first!';
                document.getElementById('subjectSemesterMsg').style.display = 'block';
            }
        });
    }
}
