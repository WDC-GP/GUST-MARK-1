// COMPLETE Enhanced Console JavaScript - No Auto-Connect Spam + Response Capture (FIXED)
// This is the complete, ready-to-use console.js file with all features preserved

// Global console state
let consoleState = {
    messages: [],
    servers: [],
    selectedServer: null,
    autoScroll: true,
    refreshInterval: null,
    pendingCommands: new Map(), // Track commands awaiting responses
    commandTimeout: 10000, // 10 second timeout for command responses
    lastCommandTime: null, // Track last command time
    liveConnections: {} // Track connection state to prevent spam
};

// Initialize console functionality
function initializeConsole() {
    console.log('🔧 Initializing ENHANCED console functionality...');
    
    loadServers();
    setupConsoleEventListeners();
    startAutoRefresh();
    
    // Display initial message
    addConsoleMessage({
        timestamp: new Date().toISOString(),
        message: 'GUST Bot Console - Ready (ENHANCED - No Auto-Connect Spam)',
        type: 'system',
        source: 'console_init'
    });

    // Start cleanup task for expired commands
    setInterval(() => {
        cleanupExpiredCommands();
    }, 30000); // Clean up every 30 seconds
}

// Clean up expired pending commands
function cleanupExpiredCommands() {
    const now = Date.now();
    for (const [commandId, commandInfo] of consoleState.pendingCommands.entries()) {
        if (now - commandInfo.timestamp > consoleState.commandTimeout) {
            consoleState.pendingCommands.delete(commandId);
        }
    }
}

// Load available servers
async function loadServers() {
    try {
        const response = await fetch('/api/servers');
        const servers = await response.json();
        
        consoleState.servers = servers || [];
        updateServerDropdown();
        
        console.log(`📡 Loaded ${servers.length} servers for console`);
    } catch (error) {
        console.error('Failed to load servers:', error);
        consoleState.servers = [];
    }
}

// Update server dropdown
function updateServerDropdown() {
    const serverSelect = document.getElementById('consoleServerSelect');
    if (!serverSelect) return;
    
    serverSelect.innerHTML = '<option value="">Select Server</option>';
    
    consoleState.servers.forEach(server => {
        const option = document.createElement('option');
        option.value = server.serverId;
        option.textContent = `${server.serverName} (${server.serverId}) - ${server.serverRegion}`;
        serverSelect.appendChild(option);
    });
    
    // Auto-select if only one server
    if (consoleState.servers.length === 1) {
        serverSelect.value = consoleState.servers[0].serverId;
        consoleState.selectedServer = consoleState.servers[0].serverId;
    }
}

// Setup event listeners
function setupConsoleEventListeners() {
    // Server selection
    const serverSelect = document.getElementById('consoleServerSelect');
    if (serverSelect) {
        serverSelect.addEventListener('change', function() {
            consoleState.selectedServer = this.value;
            refreshConsoleOutput();
        });
    }
    
    // Command input
    const commandInput = document.getElementById('consoleInput');
    if (commandInput) {
        commandInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendConsoleCommand();
            }
        });
    }
    
    // Send button
    const sendButton = document.querySelector('button[onclick="sendConsoleCommand()"]');
    if (sendButton) {
        sendButton.onclick = sendConsoleCommand;
    }
    
    // Refresh button
    const refreshButton = document.getElementById('refreshOutput');
    if (refreshButton) {
        refreshButton.onclick = refreshConsoleOutput;
    }
    
    // Quick command buttons
    setupQuickCommandButtons();
}

// Setup quick command buttons
function setupQuickCommandButtons() {
    const buttons = [
        { id: 'serverInfoBtn', command: 'serverinfo' },
        { id: 'authLevelsBtn', command: 'auth' },
        { id: 'saveServerBtn', command: 'save' },
        { id: 'sayMessageBtn', command: 'say "Server announcement from GUST Bot"' }
    ];
    
    buttons.forEach(({ id, command }) => {
        const btn = document.getElementById(id);
        if (btn) {
            btn.onclick = () => executeQuickCommand(command);
        }
    });
}

// Execute quick command
function executeQuickCommand(command) {
    const commandInput = document.getElementById('consoleInput');
    if (commandInput) {
        commandInput.value = command;
        sendConsoleCommand();
    }
}

// CRITICAL FIX: Safe message content extraction function
function getSafeMessageContent(messageObj) {
    if (!messageObj) return 'No message data';
    
    // Try different possible property names for message content
    if (messageObj.message && typeof messageObj.message === 'string' && messageObj.message.trim() !== '') {
        return messageObj.message;
    } else if (messageObj.text && typeof messageObj.text === 'string' && messageObj.text.trim() !== '') {
        return messageObj.text;
    } else if (messageObj.content && typeof messageObj.content === 'string' && messageObj.content.trim() !== '') {
        return messageObj.content;
    } else if (messageObj.command && typeof messageObj.command === 'string' && messageObj.command.trim() !== '') {
        return `> ${messageObj.command}`;
    } else if (messageObj.error && typeof messageObj.error === 'string' && messageObj.error.trim() !== '') {
        return `Error: ${messageObj.error}`;
    } else {
        // Provide meaningful fallback instead of undefined
        return `[${messageObj.type || 'system'}] System message`;
    }
}

// FIXED: Enhanced command response detection with proper null/undefined handling
function isLikelyCommandResponse(messageText, command) {
    // CRITICAL FIX: Handle undefined/null values safely
    if (!messageText || !command) {
        return false;
    }
    
    // Ensure both values are strings and handle them safely
    const msgLower = String(messageText).toLowerCase();
    const cmdLower = String(command).toLowerCase();
    
    // Specific patterns for different commands
    if (cmdLower === 'serverinfo') {
        return msgLower.includes('hostname') || 
               msgLower.includes('maxplayers') ||
               msgLower.includes('framerate') ||
               msgLower.includes('entitycount') ||
               messageText.includes('{');
    }
    
    if (cmdLower.startsWith('save')) {
        return msgLower.includes('save') || msgLower.includes('saving');
    }
    
    if (cmdLower === 'status') {
        return msgLower.includes('server') && msgLower.includes('status');
    }
    
    // General patterns
    return msgLower.includes(cmdLower) ||
           msgLower.includes('executing') ||
           msgLower.includes('command') ||
           (consoleState.lastCommandTime && 
            (Date.now() - consoleState.lastCommandTime) < 5000);
}

// FIXED: Enhanced message processing for responses with safe content handling
function processMessageForResponse(message) {
    // SAFETY CHECK: Ensure message exists
    if (!message) {
        return message;
    }
    
    // Get safe message content using the fixed function
    const messageContent = getSafeMessageContent(message);
    
    // Check if this message is a response to a pending command
    for (const [commandId, commandInfo] of consoleState.pendingCommands.entries()) {
        if (commandInfo.serverId === message.server_id && 
            (Date.now() - commandInfo.timestamp) < consoleState.commandTimeout) {
            
            // FIXED: Use safe message content and command info
            if (isLikelyCommandResponse(messageContent, commandInfo.command)) {
                // Mark as command response
                message.type = 'server_response';
                message.isCommandResponse = true;
                message.originalCommand = commandInfo.command;
                message.commandId = commandId;
                
                // Remove from pending
                consoleState.pendingCommands.delete(commandId);
                
                console.log(`📋 Captured response for command '${commandInfo.command}': ${messageContent.substring(0, 100)}...`);
                break;
            }
        }
    }
    
    return message;
}

// FIXED: Enhanced auto-connect spam filtering with safe message handling
function shouldFilterAutoConnectMessage(message) {
    // Get safe message content
    const messageContent = getSafeMessageContent(message);
    
    if (!messageContent.includes('Auto-connected to')) {
        return false;
    }
    
    // Extract server identifier
    let serverIdentifier = null;
    const parts = messageContent.split(' ');
    for (let part of parts) {
        if (part.includes('Test') || part.match(/\d+/) || part.includes('Server')) {
            serverIdentifier = part;
            break;
        }
    }
    
    if (!serverIdentifier) {
        return false;
    }
    
    const now = Date.now();
    const lastTime = consoleState.liveConnections[serverIdentifier] || 0;
    
    // Only allow one auto-connect message per server per 5 minutes
    if (now - lastTime < 300000) { // 5 minutes
        return true; // Filter this message
    }
    
    consoleState.liveConnections[serverIdentifier] = now;
    return false; // Don't filter
}

// Enhanced: Send console command with response tracking
async function sendConsoleCommand() {
    const commandInput = document.getElementById('consoleInput');
    const serverSelect = document.getElementById('consoleServerSelect');
    
    if (!commandInput || !serverSelect) {
        console.error('Console elements not found');
        return;
    }
    
    const command = commandInput.value.trim();
    const serverId = serverSelect.value;
    
    if (!command) {
        showNotification('Please enter a command', 'error');
        return;
    }
    
    if (!serverId) {
        showNotification('Please select a server', 'error');
        return;
    }
    
    // Get server region
    const server = consoleState.servers.find(s => s.serverId === serverId);
    const region = server ? server.serverRegion : 'US';
    
    // Generate unique command ID for tracking responses
    const commandId = `cmd_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // Add command to display
    addConsoleMessage({
        timestamp: new Date().toISOString(),
        message: `> ${command}`,
        type: 'command',
        source: 'user_input',
        commandId: commandId,
        serverId: serverId
    });
    
    // Track pending command for response matching
    consoleState.pendingCommands.set(commandId, {
        command: command,
        serverId: serverId,
        timestamp: Date.now(),
        expectingResponse: true
    });
    
    // Set timeout for command response
    setTimeout(() => {
        if (consoleState.pendingCommands.has(commandId)) {
            consoleState.pendingCommands.delete(commandId);
            addConsoleMessage({
                timestamp: new Date().toISOString(),
                message: `⏰ Command timeout: No response received for "${command}"`,
                type: 'warning',
                source: 'command_timeout',
                serverId: serverId
            });
        }
    }, consoleState.commandTimeout);
    
    try {
        const response = await fetch('/api/console/send', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                command: command,
                serverId: serverId,
                region: region,
                commandId: commandId  // Pass command ID for tracking
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            addConsoleMessage({
                timestamp: new Date().toISOString(),
                message: `✅ Command sent to ${server?.serverName || serverId}`,
                type: 'success',
                source: 'command_response',
                serverId: serverId
            });
            
            commandInput.value = '';
            consoleState.lastCommandTime = Date.now();
            
            // Enhanced auto-refresh to capture server response
            setTimeout(() => {
                refreshConsoleOutput();
            }, 1000);
            
            // Additional refresh to catch delayed responses
            setTimeout(() => {
                refreshConsoleOutput();
            }, 3000);
            
        } else {
            consoleState.pendingCommands.delete(commandId);
            addConsoleMessage({
                timestamp: new Date().toISOString(),
                message: `❌ Command failed: ${result.error || 'Unknown error'}`,
                type: 'error',
                source: 'command_response',
                serverId: serverId
            });
        }
    } catch (error) {
        consoleState.pendingCommands.delete(commandId);
        addConsoleMessage({
            timestamp: new Date().toISOString(),
            message: `❌ Send error: ${error.message}`,
            type: 'error',
            source: 'command_response'
        });
    }
}

// FIXED: Add console message with auto-connect spam filtering and safe handling
function addConsoleMessage(messageObj) {
    // SAFETY CHECK: Ensure messageObj exists
    if (!messageObj) {
        return;
    }
    
    // Filter out repetitive auto-connect messages using safe content extraction
    if (shouldFilterAutoConnectMessage(messageObj)) {
        return; // Skip duplicate auto-connect messages
    }
    
    // Ensure message object has required properties with safe content extraction
    const message = {
        timestamp: messageObj.timestamp || new Date().toISOString(),
        message: getSafeMessageContent(messageObj),
        type: messageObj.type || 'system',
        source: messageObj.source || 'unknown',
        server_id: messageObj.server_id || messageObj.serverId || '',
        status: messageObj.status || '',
        command: messageObj.command || '',
        response: messageObj.response || '',
        error: messageObj.error || '',
        commandId: messageObj.commandId || '',
        isCommandResponse: messageObj.isCommandResponse || false,
        originalCommand: messageObj.originalCommand || ''
    };
    
    consoleState.messages.push(message);
    
    // Keep message buffer size manageable
    if (consoleState.messages.length > 1000) {
        consoleState.messages = consoleState.messages.slice(-1000);
    }
    
    updateConsoleDisplay();
}

// Enhanced console display
function updateConsoleDisplay() {
    const outputDiv = document.getElementById('consoleOutput');
    if (!outputDiv) {
        console.error('Console output div not found');
        return;
    }
    
    const wasScrolledToBottom = outputDiv.scrollHeight - outputDiv.clientHeight <= outputDiv.scrollTop + 1;
    
    // Clear current content
    outputDiv.innerHTML = '';
    
    // Add header
    const header = document.createElement('div');
    header.className = 'text-green-400 mb-2 font-bold border-b border-gray-700 pb-2';
    header.textContent = 'GUST Bot Console - ENHANCED (No Auto-Connect Spam + Response Capture)';
    outputDiv.appendChild(header);
    
    // Display recent messages
    const recentMessages = consoleState.messages.slice(-50); // Show last 50 messages
    
    recentMessages.forEach(msg => {
        const messageDiv = createEnhancedMessageElement(msg);
        outputDiv.appendChild(messageDiv);
    });
    
    // Auto-scroll if was at bottom
    if (consoleState.autoScroll && wasScrolledToBottom) {
        outputDiv.scrollTop = outputDiv.scrollHeight;
    }
}

// FIXED: Enhanced message element creation with safe content handling
function createEnhancedMessageElement(message) {
    const div = document.createElement('div');
    div.className = 'console-message mb-1 text-sm p-2 rounded';
    
    const time = formatTimestamp(message.timestamp);
    const type = message.type || 'system';
    const typeIcon = getTypeIcon(type);
    
    // FIXED: Use safe message content extraction
    const displayMessage = getSafeMessageContent(message);
    
    // Special formatting for command responses
    if (message.isCommandResponse || type === 'server_response') {
        div.className += ' bg-gray-800 border-l-4 border-green-500';
        
        // Format JSON responses nicely
        let formattedMessage = displayMessage;
        if (displayMessage.includes('{') && displayMessage.includes('}')) {
            try {
                const jsonStart = displayMessage.indexOf('{');
                const jsonPart = displayMessage.substring(jsonStart);
                const parsed = JSON.parse(jsonPart);
                formattedMessage = displayMessage.substring(0, jsonStart) + '\n' + 
                               JSON.stringify(parsed, null, 2);
            } catch (e) {
                // Keep original if not valid JSON
            }
        }
        
        div.innerHTML = `
            <div class="flex items-center gap-2 mb-1">
                <span class="text-gray-500 text-xs">[${time}]</span>
                <span class="text-xs bg-green-700 px-2 py-1 rounded">${typeIcon} SERVER RESPONSE</span>
                ${message.originalCommand ? `<span class="text-xs text-gray-400">to: ${message.originalCommand}</span>` : ''}
            </div>
            <pre class="text-green-300 font-mono text-xs whitespace-pre-wrap">${escapeHtml(formattedMessage)}</pre>
        `;
    } else if (type === 'command') {
        div.className += ' bg-blue-900 border-l-4 border-blue-500';
        div.innerHTML = `
            <div class="flex items-center gap-2">
                <span class="text-gray-500 text-xs">[${time}]</span>
                <span class="text-xs bg-blue-700 px-2 py-1 rounded">${typeIcon} COMMAND</span>
            </div>
            <div class="text-blue-300 font-mono mt-1">${escapeHtml(displayMessage)}</div>
        `;
    } else {
        // Regular message formatting
        const colorClass = getTypeColorClass(type);
        div.className += ` ${colorClass}`;
        
        div.innerHTML = `
            <span class="text-gray-500 text-xs">[${time}]</span>
            <span class="text-xs bg-gray-700 px-1 rounded">${typeIcon} ${type}</span>
            <span class="ml-2">${escapeHtml(displayMessage)}</span>
        `;
    }
    
    return div;
}

// Get type color class
function getTypeColorClass(type) {
    const colors = {
        'error': 'text-red-400',
        'warning': 'text-yellow-400',
        'success': 'text-green-400',
        'command': 'text-blue-400',
        'server_response': 'text-green-300',
        'system': 'text-gray-300',
        'live': 'text-cyan-300'
    };
    return colors[type] || 'text-gray-300';
}

// FIXED: Refresh console output with enhanced processing
async function refreshConsoleOutput() {
    try {
        // Get console output from backend
        const response = await fetch('/api/console/output');
        const output = await response.json();
        
        if (Array.isArray(output)) {
            // Process backend messages and detect responses
            output.forEach(entry => {
                // Check if this might be a command response
                const processedEntry = processBackendMessage(entry);
                addConsoleMessage(processedEntry);
            });
        }
        
        // Also get live messages
        await loadLiveMessages();
        
        console.log(`🔄 Refreshed console: ${consoleState.messages.length} messages`);
    } catch (error) {
        console.error('Failed to refresh console output:', error);
        addConsoleMessage({
            timestamp: new Date().toISOString(),
            message: `Failed to refresh console: ${error.message}`,
            type: 'error',
            source: 'refresh_error'
        });
    }
}

// FIXED: Process backend messages for response detection with safe content handling
function processBackendMessage(entry) {
    // SAFETY CHECK: Ensure entry exists
    if (!entry) {
        return {
            timestamp: new Date().toISOString(),
            message: 'Invalid backend message',
            type: 'system',
            source: 'backend_error'
        };
    }
    
    // Get safe message content from entry
    const messageText = getSafeMessageContent(entry);
    
    // Check if this matches any pending command
    for (const [commandId, commandInfo] of consoleState.pendingCommands.entries()) {
        if (entry.server_id === commandInfo.serverId) {
            if (isLikelyCommandResponse(messageText, commandInfo.command)) {
                // Mark as command response
                consoleState.pendingCommands.delete(commandId);
                return {
                    timestamp: entry.timestamp || new Date().toISOString(),
                    message: messageText,
                    type: 'server_response',
                    source: 'backend_response',
                    server_id: entry.server_id || '',
                    isCommandResponse: true,
                    originalCommand: commandInfo.command,
                    status: entry.status || '',
                    command: entry.command || ''
                };
            }
        }
    }
    
    // Regular backend message
    return {
        timestamp: entry.timestamp || new Date().toISOString(),
        message: messageText,
        type: entry.type || 'system',
        source: entry.source || 'backend',
        server_id: entry.server_id || entry.serverId || '',
        command: entry.command || '',
        status: entry.status || ''
    };
}

// Load live messages
async function loadLiveMessages() {
    try {
        const params = new URLSearchParams();
        if (consoleState.selectedServer) {
            params.append('serverId', consoleState.selectedServer);
        }
        params.append('limit', '20');
        
        const response = await fetch(`/api/console/live/messages?${params}`);
        const data = await response.json();
        
        if (data.messages && Array.isArray(data.messages)) {
            // Process live messages for command responses
            data.messages.forEach(msg => {
                const processedMsg = processMessageForResponse(msg);
                addConsoleMessage(processedMsg);
            });
        }
    } catch (error) {
        console.warn('Failed to load live messages:', error);
    }
}

// Start auto-refresh
function startAutoRefresh() {
    if (consoleState.refreshInterval) {
        clearInterval(consoleState.refreshInterval);
    }
    
    consoleState.refreshInterval = setInterval(() => {
        refreshConsoleOutput();
    }, 5000); // Refresh every 5 seconds
    
    console.log('🔄 Auto-refresh started (5s interval)');
}

// Utility functions
function formatTimestamp(timestamp) {
    try {
        return new Date(timestamp).toLocaleTimeString();
    } catch {
        return new Date().toLocaleTimeString();
    }
}

function getTypeIcon(type) {
    const icons = {
        'command': '🔧',
        'success': '✅',
        'error': '❌',
        'warning': '⚠️',
        'system': '🖥️',
        'chat': '💬',
        'event': '🎯',
        'live': '📡',
        'auth': '🔐',
        'save': '💾',
        'server_response': '📋'
    };
    return icons[type] || '📋';
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    // Simple notification - can be enhanced with toast library
    const className = type === 'error' ? 'text-red-400' : 'text-green-400';
    console.log(`[${type.toUpperCase()}] ${message}`);
    
    // Also add to console output
    addConsoleMessage({
        timestamp: new Date().toISOString(),
        message: message,
        type: type,
        source: 'notification'
    });
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit for other scripts to load
    setTimeout(initializeConsole, 1000);
});

// Backward compatibility functions (if called from HTML)
window.sendConsoleCommand = sendConsoleCommand;
window.refreshConsoleOutput = refreshConsoleOutput;
window.executeQuickCommand = executeQuickCommand;

console.log('✅ ENHANCED Console JavaScript loaded - Auto-connect spam filtered + Response capture enabled (FIXED)');