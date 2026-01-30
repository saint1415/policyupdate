// PolicyUpdate GRC Platform - JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('PolicyUpdate GRC Platform loaded');
});

// API helper
async function apiCall(endpoint, options = {}) {
    const response = await fetch(`/api${endpoint}`, {
        headers: {
            'Content-Type': 'application/json',
            ...options.headers
        },
        ...options
    });
    return response.json();
}

// Load frameworks
async function loadFrameworks() {
    const data = await apiCall('/frameworks');
    return data;
}

// Load policies
async function loadPolicies() {
    const data = await apiCall('/policies');
    return data;
}

// Search policies
async function searchPolicies(query) {
    const data = await apiCall(`/policies/search?q=${encodeURIComponent(query)}`);
    return data;
}

// Generate package
async function generatePackage(clientName, frameworks, format) {
    const data = await apiCall('/generate', {
        method: 'POST',
        body: JSON.stringify({
            client_name: clientName,
            frameworks: frameworks,
            format: format
        })
    });
    return data;
}

// Format date
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}
