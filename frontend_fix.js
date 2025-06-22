/**
 * EMERGENCY FIX for "Cannot read properties of undefined (reading 'serverId')" Error
 * =================================================================================
 * 
 * Add this code to your templates/scripts/server_manager.js.html file
 * or replace the existing server addition response handling
 */

/**
 * 🚨 SAFE SERVER RESPONSE HANDLER - Prevents undefined property access
 */
function safelyHandleServerResponse(result) {
    console.log('🛡️ Safely handling server response:', result);
    
    try {
        // Check if result exists and is valid
        if (!result) {
            throw new Error('No response received from server');
        }
        
        // Check if the operation was successful
        if (!result.success) {
            throw new Error(result.error || 'Server operation failed');
        }
        
        // Safely extract server data with fallbacks
        const serverData = result.server_data || result.serverData || {};
        const discovery = result.discovery || {};
        
        // Safely extract properties with null checks
        const serverId = serverData.serverId || serverData.server_id || 'Unknown';
        const serviceId = serverData.serviceId || serverData.service_id || null;
        const serverName = serverData.serverName || serverData.server_name || 'Unnamed Server';
        const serverRegion = serverData.serverRegion || serverData.server_region || 'US';
        
        // Safe discovery status extraction
        const discoveryStatus = discovery.status || serverData.discovery_status || 'unknown';
        const discoveryMessage = discovery.message || serverData.discovery_message || 'No discovery information';
        
        console.log('✅ Safely extracted server data:', {
            serverId,
            serviceId,
            serverName,
            serverRegion,
            discoveryStatus,
            discoveryMessage
        });
        
        // Display appropriate success message based on discovery status
        if (discoveryStatus === 'success' && serviceId) {
            showSuccessMessage(`✅ Server "${serverName}" added successfully!
                🆔 Server ID: ${serverId}
                🔧 Service ID: ${serviceId}
                🌍 Region: ${serverRegion}
                🎯 Status: Full functionality enabled`);
        } else if (discoveryStatus === 'failed' || !serviceId) {
            showWarningMessage(`⚠️ Server "${serverName}" added with limited functionality
                🆔 Server ID: ${serverId}
                ❌ Service ID: Not discovered (${discoveryMessage})
                🌍 Region: ${serverRegion}
                📊 Health monitoring: ✅ Available
                💻 Commands: ❌ Limited (no Service ID)`);
        } else {
            showInfoMessage(`ℹ️ Server "${serverName}" added
                🆔 Server ID: ${serverId}
                🔧 Service ID: ${serviceId || 'Unknown'}
                🌍 Region: ${serverRegion}
                📊 Status: ${discoveryStatus}`);
        }
        
        return {
            success: true,
            serverId,
            serviceId,
            serverName,
            serverRegion,
            discoveryStatus,
            discoveryMessage
        };
        
    } catch (error) {
        console.error('❌ Error safely handling server response:', error);
        showErrorMessage(`❌ Error processing server response: ${error.message}`);
        
        return {
            success: false,
            error: error.message
        };
    }
}

/**
 * 🔧 ENHANCED ADD SERVER FUNCTION - With Safe Response Handling
 */
async function addNewServerSafe() {
    console.log('🚀 Adding new server with safe error handling...');
    
    const btn = document.getElementById('addServerBtn');
    const status = document.getElementById('addServerStatus');
    
    // Set loading state
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '🔍 Adding Server...';
    }
    
    try {
        // Get form data safely
        const formData = getServerFormDataSafe();
        
        if (!formData.valid) {
            throw new Error(formData.error);
        }
        
        // Show processing status
        if (status) {
            status.innerHTML = '<div class="text-blue-400">🔍 Discovering Service ID...</div>';
        }
        
        console.log('📤 Sending server addition request:', formData.data);
        
        // Make API call with enhanced error handling
        const response = await fetch('/api/servers/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin',
            body: JSON.stringify(formData.data)
        });
        
        // Check response status
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        // Parse response safely
        let result;
        try {
            result = await response.json();
        } catch (parseError) {
            throw new Error(`Failed to parse server response: ${parseError.message}`);
        }
        
        console.log('📥 Received server response:', result);
        
        // Use safe response handler
        const handledResult = safelyHandleServerResponse(result);
        
        if (handledResult.success) {
            // Clear form on success
            clearServerFormSafe();
            
            // Reload server list
            try {
                await loadManagedServers();
            } catch (loadError) {
                console.warn('⚠️ Failed to reload server list:', loadError);
            }
            
            // Show final status
            if (status) {
                if (handledResult.serviceId) {
                    status.innerHTML = `<div class="text-green-400">✅ Server added with full functionality!</div>`;
                } else {
                    status.innerHTML = `<div class="text-yellow-400">⚠️ Server added (limited functionality - no Service ID)</div>`;
                }
            }
            
        } else {
            throw new Error(handledResult.error || 'Failed to process server response');
        }
        
    } catch (error) {
        console.error('❌ Add server error:', error);
        
        // Show error message
        showErrorMessage(`Failed to add server: ${error.message}`);
        
        if (status) {
            status.innerHTML = `<div class="text-red-400">❌ Error: ${error.message}</div>`;
        }
        
    } finally {
        // Reset button state
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '➕ Add Server';
        }
    }
}

/**
 * 🛡️ SAFE FORM DATA EXTRACTION - Prevents undefined errors
 */
function getServerFormDataSafe() {
    try {
        const serverId = document.getElementById('newServerId')?.value?.trim() || '';
        const serverName = document.getElementById('newServerName')?.value?.trim() || '';
        const serverRegion = document.getElementById('newServerRegion')?.value || 'US';
        const serverType = document.getElementById('newServerType')?.value || 'Rust';
        const description = document.getElementById('newServerDescription')?.value?.trim() || '';
        
        // Validation
        if (!serverId) {
            return { valid: false, error: 'Server ID is required' };
        }
        
        if (!serverName) {
            return { valid: false, error: 'Server Name is required' };
        }
        
        if (!/^\d+$/.test(serverId)) {
            return { valid: false, error: 'Server ID must be numeric' };
        }
        
        return {
            valid: true,
            data: {
                serverId,
                serverName,
                serverRegion,
                serverType,
                description
            }
        };
        
    } catch (error) {
        return { valid: false, error: `Form data extraction error: ${error.message}` };
    }
}

/**
 * 🧹 SAFE FORM CLEARING - Prevents errors on missing elements
 */
function clearServerFormSafe() {
    try {
        const formFields = [
            'newServerId',
            'newServerName', 
            'newServerDescription'
        ];
        
        formFields.forEach(fieldId => {
            const field = document.getElementById(fieldId);
            if (field) {
                field.value = '';
            }
        });
        
        // Reset select fields to default
        const regionField = document.getElementById('newServerRegion');
        if (regionField) {
            regionField.value = 'US';
        }
        
        const typeField = document.getElementById('newServerType');
        if (typeField) {
            typeField.value = 'Rust';
        }
        
        console.log('✅ Form cleared safely');
        
    } catch (error) {
        console.warn('⚠️ Error clearing form (non-critical):', error);
    }
}

/**
 * 📢 SAFE MESSAGE DISPLAY FUNCTIONS
 */
function showSuccessMessage(message) {
    console.log('✅ SUCCESS:', message);
    // Add your success notification logic here
    if (typeof addLiveConsoleMessage === 'function') {
        addLiveConsoleMessage(message, '', 'success');
    }
}

function showWarningMessage(message) {
    console.log('⚠️ WARNING:', message);
    // Add your warning notification logic here
    if (typeof addLiveConsoleMessage === 'function') {
        addLiveConsoleMessage(message, '', 'warning');
    }
}

function showInfoMessage(message) {
    console.log('ℹ️ INFO:', message);
    // Add your info notification logic here
    if (typeof addLiveConsoleMessage === 'function') {
        addLiveConsoleMessage(message, '', 'info');
    }
}

function showErrorMessage(message) {
    console.log('❌ ERROR:', message);
    // Add your error notification logic here
    if (typeof addLiveConsoleMessage === 'function') {
        addLiveConsoleMessage(message, '', 'error');
    }
}

/**
 * 🔄 REPLACE YOUR EXISTING ADD SERVER FUNCTION
 * 
 * Replace your existing addNewServer function with addNewServerSafe,
 * or add this code to handle the response more safely.
 */

// If you want to keep your existing function name, you can do:
// window.addNewServer = addNewServerSafe;

/**
 * 🚨 EMERGENCY PATCH - Add this to immediately fix the error
 */
if (typeof window !== 'undefined') {
    // Backup original function if it exists
    if (typeof window.addNewServer === 'function') {
        window.addNewServerOriginal = window.addNewServer;
    }
    
    // Replace with safe version
    window.addNewServer = addNewServerSafe;
    
    console.log('🛡️ Emergency patch applied - addNewServer replaced with safe version');
}
