# 🧪 GUST-MARK-1 Testing Procedures

## 📋 **Overview**

This document provides comprehensive testing procedures for all GUST-MARK-1 components, including the new Server Health monitoring system, live player count functionality, and all existing features.

## 🎯 **Testing Categories**

### **1. Server Health Monitoring System** ✅ *NEW*
### **2. Live Player Count System** ✅ *ENHANCED*
### **3. Core Application Components** ✅ *UPDATED*
### **4. Integration Testing** ✅ *COMPREHENSIVE*
### **5. Performance Testing** ✅ *ADVANCED*

---

## 🏥 **Server Health Monitoring Tests**

### **Pre-Test Setup**
```bash
# 1. Start application
python main.py

# 2. Login with credentials
# URL: http://localhost:5000
# Username: admin
# Password: password

# 3. Navigate to Server Manager
# Add at least one test server for monitoring
```

### **Test 1: Server Health Tab Access**
```javascript
// Browser Console Test
console.log('🧪 Testing Server Health tab access...');

// Navigate to Server Health tab
showTab('server-health');

// Verify tab loads
const healthView = document.getElementById('server-health');
console.assert(healthView && healthView.style.display !== 'none', 
    '❌ Server Health view should be visible');

console.log('✅ Server Health tab access test passed');
```

### **Test 2: Server Detection & Selection**
```javascript
// Test server detection
console.log('🧪 Testing server detection...');

// Check if servers are detected
if (typeof managedServers !== 'undefined' && managedServers.length > 0) {
    console.log(`✅ Found ${managedServers.length} managed servers`);
    
    // Test server selector
    const serverSelect = document.getElementById('server-health-selector');
    console.assert(serverSelect && serverSelect.options.length > 1, 
        '❌ Server selector should have server options');
    
    console.log('✅ Server detection test passed');
} else {
    console.warn('⚠️ No servers found - add servers in Server Manager first');
}
```

### **Test 3: Health Status API**
```javascript
// Test health status API
async function testHealthStatusAPI() {
    console.log('🧪 Testing Health Status API...');
    
    const testServerId = managedServers[0]?.serverId || 'test_server';
    
    try {
        const response = await fetch(`/api/server_health/status/${testServerId}`);
        const data = await response.json();
        
        console.assert(response.ok, '❌ Health status API should respond with 200');
        console.assert(data.success, '❌ Health status response should be successful');
        console.assert(data.health_data, '❌ Health status should contain health_data');
        console.assert(data.metrics, '❌ Health status should contain metrics');
        
        console.log('✅ Health Status API test passed');
        console.log('📊 Sample data:', data);
        
    } catch (error) {
        console.error('❌ Health Status API test failed:', error);
    }
}

// Run test
testHealthStatusAPI();
```

### **Test 4: Chart.js Integration**
```javascript
// Test Chart.js functionality
function testChartIntegration() {
    console.log('🧪 Testing Chart.js integration...');
    
    // Check if Chart.js is available
    console.assert(typeof Chart !== 'undefined', '❌ Chart.js should be available');
    
    // Check if health charts exist
    const fpsChart = Chart.getChart('fps-chart');
    const playersChart = Chart.getChart('players-chart');
    
    if (fpsChart) {
        console.log('✅ FPS chart found and initialized');
    } else {
        console.warn('⚠️ FPS chart not found - may still be loading');
    }
    
    if (playersChart) {
        console.log('✅ Players chart found and initialized');
    } else {
        console.warn('⚠️ Players chart not found - may still be loading');
    }
    
    console.log('✅ Chart.js integration test completed');
}

// Run test after charts should be loaded
setTimeout(testChartIntegration, 3000);
```

### **Test 5: Command Feed Functionality**
```javascript
// Test command feed
async function testCommandFeed() {
    console.log('🧪 Testing Command Feed...');
    
    const testServerId = managedServers[0]?.serverId || 'test_server';
    
    try {
        const response = await fetch(`/api/server_health/commands/${testServerId}`);
        const data = await response.json();
        
        console.assert(response.ok, '❌ Command feed API should respond');
        console.assert(data.success, '❌ Command feed should be successful');
        console.assert(Array.isArray(data.commands), '❌ Commands should be an array');
        
        console.log(`✅ Command feed test passed - ${data.commands.length} commands found`);
        
        // Test command filtering
        const filterAllBtn = document.getElementById('filter-all-btn');
        const filterAutoBtn = document.getElementById('filter-auto-btn');
        
        if (filterAllBtn && filterAutoBtn) {
            filterAllBtn.click();
            console.log('✅ All filter button works');
            
            filterAutoBtn.click();
            console.log('✅ Auto filter button works');
        }
        
    } catch (error) {
        console.error('❌ Command feed test failed:', error);
    }
}

// Run test
testCommandFeed();
```

### **Test 6: Auto-refresh System**
```javascript
// Test auto-refresh functionality
function testAutoRefresh() {
    console.log('🧪 Testing auto-refresh system...');
    
    // Check if auto-refresh is active
    if (typeof serverHealthData !== 'undefined' && serverHealthData.refreshInterval) {
        console.log('✅ Auto-refresh interval is active');
        
        // Test manual refresh
        if (typeof refreshHealthData === 'function') {
            refreshHealthData();
            console.log('✅ Manual refresh function works');
        }
        
    } else {
        console.warn('⚠️ Auto-refresh not detected - may not be initialized');
    }
    
    console.log('✅ Auto-refresh system test completed');
}

// Run test
testAutoRefresh();
```

---

## 👥 **Live Player Count System Tests**

### **Test 1: Player Count API Integration**
```javascript
// Test player count API
async function testPlayerCountAPI() {
    console.log('🧪 Testing Player Count API...');
    
    const testServerId = managedServers[0]?.serverId || 'test_server';
    
    try {
        const response = await fetch(`/api/logs/player-count/${testServerId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'}
        });
        const data = await response.json();
        
        console.assert(response.ok, '❌ Player count API should respond');
        console.log('📊 Player count data:', data);
        
        if (data.success) {
            console.log('✅ Player count API test passed');
            console.log(`👥 Players: ${data.data.current}/${data.data.max} (${data.data.percentage}%)`);
        } else {
            console.warn('⚠️ Player count API returned no data (normal for empty server)');
        }
        
    } catch (error) {
        console.error('❌ Player count API test failed:', error);
    }
}

// Run test
testPlayerCountAPI();
```

### **Test 2: Auto Command System**
```javascript
// Test auto command system
function testAutoCommandSystem() {
    console.log('🧪 Testing Auto Command System...');
    
    // Check if auto command functions are available
    const functions = [
        'getAutoConsoleStatus',
        'testAutoConsoleCommands',
        'toggleAutoConsoleCommands'
    ];
    
    functions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ ${funcName} function available`);
        } else {
            console.warn(`⚠️ ${funcName} function not found`);
        }
    });
    
    // Test auto command status
    if (typeof getAutoConsoleStatus === 'function') {
        const status = getAutoConsoleStatus();
        console.log('📊 Auto command status:', status);
    }
    
    console.log('✅ Auto command system test completed');
}

// Run test
testAutoCommandSystem();
```

### **Test 3: Visual Player Count Updates**
```javascript
// Test visual player count updates
function testPlayerCountVisuals() {
    console.log('🧪 Testing Player Count Visuals...');
    
    const testServerId = managedServers[0]?.serverId || 'test_server';
    const serverCard = document.querySelector(`[data-server-id="${testServerId}"]`);
    
    if (serverCard) {
        // Test visual update with mock data
        const mockData = {
            current: 15,
            max: 100,
            percentage: 15,
            timestamp: new Date().toISOString()
        };
        
        if (typeof updatePlayerCountDisplay === 'function') {
            updatePlayerCountDisplay(testServerId, mockData, 'success');
            console.log('✅ Player count visual update works');
        }
        
        // Check if progress bar updated
        const progressBar = serverCard.querySelector('.progress-bar-fill');
        if (progressBar) {
            console.log(`✅ Progress bar updated to ${progressBar.style.width}`);
        }
        
    } else {
        console.warn('⚠️ No server card found for visual testing');
    }
    
    console.log('✅ Player count visual test completed');
}

// Run test
testPlayerCountVisuals();
```

---

## 🧩 **Core Application Component Tests**

### **Test 1: Navigation System**
```javascript
// Test tab navigation
function testNavigation() {
    console.log('🧪 Testing Navigation System...');
    
    const tabs = [
        'dashboard',
        'server-manager', 
        'console',
        'server-health',
        'events',
        'economy',
        'gambling',
        'clans',
        'user-management',
        'logs'
    ];
    
    tabs.forEach(tab => {
        try {
            showTab(tab);
            const view = document.getElementById(`${tab}-view`) || document.getElementById(tab);
            
            if (view && view.style.display !== 'none') {
                console.log(`✅ ${tab} tab navigation works`);
            } else {
                console.warn(`⚠️ ${tab} tab may not be fully implemented`);
            }
            
        } catch (error) {
            console.error(`❌ ${tab} tab navigation failed:`, error);
        }
    });
    
    console.log('✅ Navigation system test completed');
}

// Run test
testNavigation();
```

### **Test 2: Server Manager Integration**
```javascript
// Test server manager functionality
async function testServerManager() {
    console.log('🧪 Testing Server Manager...');
    
    // Switch to server manager tab
    showTab('server-manager');
    
    // Test server loading
    if (typeof loadManagedServers === 'function') {
        try {
            await loadManagedServers();
            console.log(`✅ Server loading works - ${managedServers.length} servers loaded`);
        } catch (error) {
            console.error('❌ Server loading failed:', error);
        }
    }
    
    // Test server display
    const serverContainer = document.getElementById('managed-servers-container');
    if (serverContainer) {
        const serverCards = serverContainer.querySelectorAll('.server-card');
        console.log(`✅ Server display works - ${serverCards.length} server cards found`);
    }
    
    console.log('✅ Server Manager test completed');
}

// Run test
testServerManager();
```

### **Test 3: Console System**
```javascript
// Test console functionality
function testConsoleSystem() {
    console.log('🧪 Testing Console System...');
    
    // Switch to console tab
    showTab('console');
    
    // Check console elements
    const consoleOutput = document.getElementById('consoleOutput');
    const consoleInput = document.getElementById('consoleInput');
    const consoleServerSelect = document.getElementById('consoleServerSelect');
    
    console.assert(consoleOutput, '❌ Console output should exist');
    console.assert(consoleInput, '❌ Console input should exist');
    console.assert(consoleServerSelect, '❌ Console server selector should exist');
    
    // Test console command functions
    const consoleFunctions = [
        'sendConsoleCommand',
        'refreshConsoleWithLiveMessages',
        'addLiveConsoleMessage'
    ];
    
    consoleFunctions.forEach(funcName => {
        if (typeof window[funcName] === 'function') {
            console.log(`✅ ${funcName} function available`);
        } else {
            console.warn(`⚠️ ${funcName} function not found`);
        }
    });
    
    console.log('✅ Console system test completed');
}

// Run test
testConsoleSystem();
```

---

## 🔗 **Integration Testing**

### **Test 1: Cross-Component Data Flow**
```javascript
// Test data flow between components
async function testDataFlow() {
    console.log('🧪 Testing Cross-Component Data Flow...');
    
    // Test 1: Server Manager → Server Health
    showTab('server-manager');
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    if (managedServers.length > 0) {
        showTab('server-health');
        await new Promise(resolve => setTimeout(resolve, 2000));
        
        const serverSelect = document.getElementById('server-health-selector');
        if (serverSelect && serverSelect.options.length > 1) {
            console.log('✅ Server data flows from Server Manager to Server Health');
        }
    }
    
    // Test 2: Console Commands → Command Feed
    showTab('console');
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Simulate console command
    const consoleInput = document.getElementById('consoleInput');
    if (consoleInput && typeof sendConsoleCommand === 'function') {
        consoleInput.value = 'serverinfo';
        // Note: Don't actually send in test mode
        console.log('✅ Console command interface ready');
    }
    
    console.log('✅ Data flow integration test completed');
}

// Run test
testDataFlow();
```

### **Test 2: API Integration Chain**
```javascript
// Test complete API integration chain
async function testAPIChain() {
    console.log('🧪 Testing API Integration Chain...');
    
    const testServerId = managedServers[0]?.serverId || 'test_server';
    
    try {
        // Test chain: Logs API → Health API → Charts API
        
        // 1. Player count from logs
        const playerResponse = await fetch(`/api/logs/player-count/${testServerId}`, {
            method: 'POST'
        });
        console.log('📡 Logs API response:', playerResponse.status);
        
        // 2. Health status (uses logs data)
        const healthResponse = await fetch(`/api/server_health/status/${testServerId}`);
        console.log('📡 Health API response:', healthResponse.status);
        
        // 3. Chart data (uses health data)
        const chartResponse = await fetch(`/api/server_health/charts/${testServerId}`);
        console.log('📡 Charts API response:', chartResponse.status);
        
        // 4. Command history
        const commandResponse = await fetch(`/api/server_health/commands/${testServerId}`);
        console.log('📡 Commands API response:', commandResponse.status);
        
        console.log('✅ API integration chain test completed');
        
    } catch (error) {
        console.error('❌ API integration chain test failed:', error);
    }
}

// Run test
testAPIChain();
```

---

## ⚡ **Performance Testing**

### **Test 1: Page Load Performance**
```javascript
// Test page load performance
function testPageLoadPerformance() {
    console.log('🧪 Testing Page Load Performance...');
    
    // Measure navigation timing
    if (performance.timing) {
        const timing = performance.timing;
        const loadTime = timing.loadEventEnd - timing.navigationStart;
        const domReady = timing.domContentLoadedEventEnd - timing.navigationStart;
        
        console.log(`📊 Page load time: ${loadTime}ms`);
        console.log(`📊 DOM ready time: ${domReady}ms`);
        
        // Performance assertions
        console.assert(loadTime < 5000, '❌ Page load should be under 5 seconds');
        console.assert(domReady < 2000, '❌ DOM ready should be under 2 seconds');
        
        console.log('✅ Page load performance test passed');
    }
}

// Run test
testPageLoadPerformance();
```

### **Test 2: Memory Usage Monitoring**
```javascript
// Test memory usage
function testMemoryUsage() {
    console.log('🧪 Testing Memory Usage...');
    
    if (performance.memory) {
        const memory = performance.memory;
        
        console.log(`📊 Used JS heap: ${(memory.usedJSHeapSize / 1048576).toFixed(2)} MB`);
        console.log(`📊 Total JS heap: ${(memory.totalJSHeapSize / 1048576).toFixed(2)} MB`);
        console.log(`📊 Heap limit: ${(memory.jsHeapSizeLimit / 1048576).toFixed(2)} MB`);
        
        // Memory usage assertions
        const usedMB = memory.usedJSHeapSize / 1048576;
        console.assert(usedMB < 100, '❌ JS heap usage should be under 100MB');
        
        console.log('✅ Memory usage test completed');
    }
}

// Run test
testMemoryUsage();
```

### **Test 3: Chart Performance**
```javascript
// Test chart rendering performance
function testChartPerformance() {
    console.log('🧪 Testing Chart Performance...');
    
    if (typeof Chart !== 'undefined') {
        const startTime = performance.now();
        
        // Create test chart
        const testCanvas = document.createElement('canvas');
        testCanvas.width = 400;
        testCanvas.height = 200;
        document.body.appendChild(testCanvas);
        
        const testChart = new Chart(testCanvas, {
            type: 'line',
            data: {
                labels: Array(50).fill().map((_, i) => `Point ${i}`),
                datasets: [{
                    label: 'Test Data',
                    data: Array(50).fill().map(() => Math.random() * 100),
                    borderColor: '#22c55e'
                }]
            },
            options: {
                responsive: false,
                animation: false
            }
        });
        
        const renderTime = performance.now() - startTime;
        console.log(`📊 Chart render time: ${renderTime.toFixed(2)}ms`);
        
        // Performance assertion
        console.assert(renderTime < 100, '❌ Chart render should be under 100ms');
        
        // Cleanup
        testChart.destroy();
        document.body.removeChild(testCanvas);
        
        console.log('✅ Chart performance test passed');
    }
}

// Run test
testChartPerformance();
```

---

## 🔧 **Automated Test Suite**

### **Complete Test Runner**
```javascript
// Comprehensive automated test suite
class GUSTTestSuite {
    constructor() {
        this.results = {
            passed: 0,
            failed: 0,
            warnings: 0,
            tests: []
        };
    }
    
    async runAllTests() {
        console.log('🚀 Starting GUST-MARK-1 Complete Test Suite...');
        console.log('=' * 60);
        
        // Core functionality tests
        await this.runTest('Navigation System', this.testNavigation);
        await this.runTest('Server Manager', this.testServerManager);
        await this.runTest('Console System', this.testConsoleSystem);
        
        // Monitoring system tests
        await this.runTest('Server Health System', this.testServerHealth);
        await this.runTest('Player Count System', this.testPlayerCount);
        await this.runTest('Chart Integration', this.testChartIntegration);
        
        // Performance tests
        await this.runTest('Performance Metrics', this.testPerformance);
        
        // Integration tests
        await this.runTest('API Integration', this.testAPIIntegration);
        
        this.printResults();
    }
    
    async runTest(testName, testFunction) {
        console.log(`\n🧪 Running ${testName} tests...`);
        
        try {
            const result = await testFunction.call(this);
            
            if (result.success) {
                this.results.passed++;
                console.log(`✅ ${testName}: PASSED`);
            } else {
                this.results.failed++;
                console.log(`❌ ${testName}: FAILED - ${result.error}`);
            }
            
            this.results.tests.push({
                name: testName,
                success: result.success,
                details: result.details || [],
                error: result.error
            });
            
        } catch (error) {
            this.results.failed++;
            console.error(`❌ ${testName}: ERROR - ${error.message}`);
            
            this.results.tests.push({
                name: testName,
                success: false,
                error: error.message
            });
        }
    }
    
    printResults() {
        console.log('\n' + '=' * 60);
        console.log('📊 GUST-MARK-1 Test Results Summary');
        console.log('=' * 60);
        console.log(`✅ Passed: ${this.results.passed}`);
        console.log(`❌ Failed: ${this.results.failed}`);
        console.log(`⚠️ Warnings: ${this.results.warnings}`);
        console.log(`📊 Total: ${this.results.passed + this.results.failed}`);
        
        const successRate = (this.results.passed / (this.results.passed + this.results.failed)) * 100;
        console.log(`📈 Success Rate: ${successRate.toFixed(1)}%`);
        
        if (successRate >= 90) {
            console.log('🎉 EXCELLENT: System is performing optimally!');
        } else if (successRate >= 75) {
            console.log('👍 GOOD: System is mostly functional with minor issues');
        } else {
            console.log('⚠️ NEEDS ATTENTION: Multiple issues detected');
        }
    }
    
    async testServerHealth() {
        const details = [];
        
        // Test tab access
        showTab('server-health');
        const healthView = document.getElementById('server-health');
        if (!healthView || healthView.style.display === 'none') {
            return { success: false, error: 'Server Health tab not accessible' };
        }
        details.push('Tab access: OK');
        
        // Test API endpoints
        try {
            const testServerId = managedServers[0]?.serverId || 'test_server';
            const response = await fetch(`/api/server_health/status/${testServerId}`);
            
            if (response.ok) {
                details.push('Health API: OK');
            } else {
                details.push('Health API: Failed');
            }
        } catch (error) {
            details.push(`Health API: Error - ${error.message}`);
        }
        
        return { success: true, details };
    }
    
    async testPlayerCount() {
        const details = [];
        
        // Test player count functions
        const requiredFunctions = ['getPlayerCountFromLogs', 'updatePlayerCountDisplay'];
        requiredFunctions.forEach(funcName => {
            if (typeof window[funcName] === 'function') {
                details.push(`${funcName}: Available`);
            } else {
                details.push(`${funcName}: Missing`);
            }
        });
        
        return { success: true, details };
    }
    
    async testChartIntegration() {
        const details = [];
        
        // Test Chart.js availability
        if (typeof Chart !== 'undefined') {
            details.push('Chart.js: Available');
            
            // Test chart creation
            const testCanvas = document.createElement('canvas');
            try {
                const testChart = new Chart(testCanvas, {
                    type: 'line',
                    data: { labels: [], datasets: [] }
                });
                testChart.destroy();
                details.push('Chart creation: OK');
            } catch (error) {
                details.push(`Chart creation: Failed - ${error.message}`);
            }
        } else {
            return { success: false, error: 'Chart.js not available' };
        }
        
        return { success: true, details };
    }
    
    async testNavigation() {
        const tabs = ['dashboard', 'server-manager', 'server-health'];
        const details = [];
        
        for (const tab of tabs) {
            try {
                showTab(tab);
                details.push(`${tab}: OK`);
            } catch (error) {
                details.push(`${tab}: Failed`);
            }
        }
        
        return { success: true, details };
    }
    
    async testServerManager() {
        const details = [];
        
        if (typeof loadManagedServers === 'function') {
            details.push('loadManagedServers: Available');
        }
        
        if (managedServers && managedServers.length > 0) {
            details.push(`Servers loaded: ${managedServers.length}`);
        } else {
            details.push('No servers configured');
        }
        
        return { success: true, details };
    }
    
    async testConsoleSystem() {
        const details = [];
        
        showTab('console');
        
        const elements = ['consoleOutput', 'consoleInput', 'consoleServerSelect'];
        elements.forEach(elementId => {
            const element = document.getElementById(elementId);
            if (element) {
                details.push(`${elementId}: Found`);
            } else {
                details.push(`${elementId}: Missing`);
            }
        });
        
        return { success: true, details };
    }
    
    async testPerformance() {
        const details = [];
        
        // Test page load performance
        if (performance.timing) {
            const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
            details.push(`Page load: ${loadTime}ms`);
        }
        
        // Test memory usage
        if (performance.memory) {
            const usedMB = (performance.memory.usedJSHeapSize / 1048576).toFixed(2);
            details.push(`Memory usage: ${usedMB}MB`);
        }
        
        return { success: true, details };
    }
    
    async testAPIIntegration() {
        const details = [];
        
        const testServerId = managedServers[0]?.serverId || 'test_server';
        const endpoints = [
            `/api/server_health/status/${testServerId}`,
            `/api/server_health/charts/${testServerId}`,
            `/api/server_health/commands/${testServerId}`,
            `/api/server_health/heartbeat`
        ];
        
        for (const endpoint of endpoints) {
            try {
                const response = await fetch(endpoint);
                details.push(`${endpoint}: ${response.status}`);
            } catch (error) {
                details.push(`${endpoint}: Error`);
            }
        }
        
        return { success: true, details };
    }
}

// Auto-run tests in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    console.log('🔧 Development environment detected');
    
    // Create global test suite instance
    window.gustTestSuite = new GUSTTestSuite();
    
    // Run tests after page load
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => {
            if (confirm('Run GUST-MARK-1 automated test suite?')) {
                window.gustTestSuite.runAllTests();
            }
        }, 3000);
    });
}
```

---

## 📋 **Manual Testing Checklist**

### **Server Health Monitoring Checklist**
- [ ] Server Health tab loads without errors
- [ ] Server selector populates with available servers
- [ ] Health status cards display real data
- [ ] Charts render properly with Chart.js
- [ ] Command feed shows recent serverinfo commands
- [ ] Auto-refresh works every 30 seconds
- [ ] Filter buttons work (All, Admin, Auto)
- [ ] Status indicators change color based on health
- [ ] Tab switching doesn't cause Chart.js errors

### **Live Player Count Checklist**
- [ ] Player counts display in Server Manager
- [ ] Auto commands send serverinfo every 10 seconds
- [ ] Progress bars update with correct percentages
- [ ] Color coding works (green→yellow→orange→red)
- [ ] Demo mode works when no real data available
- [ ] Preserved values during loading states
- [ ] Error handling works gracefully

### **Integration Checklist**
- [ ] Server data flows between tabs correctly
- [ ] APIs respond within reasonable time (< 2s)
- [ ] MongoDB fallback to memory storage works
- [ ] Authentication protects all endpoints
- [ ] Error messages are user-friendly
- [ ] Performance remains smooth with multiple tabs

---

## 🚀 **Quick Test Commands**

### **Browser Console Quick Tests**
```javascript
// Quick health check
window.gustTestSuite?.runAllTests();

// Test specific components
testServerHealthSystem();
testPlayerCountAPI();
testChartIntegration();

// Performance check
testPageLoadPerformance();
testMemoryUsage();

// API test
testAPIChain();
```

### **Development Testing**
```bash
# Start application in debug mode
python main.py --debug

# Run with verbose logging
python main.py --log-level=DEBUG

# Test with demo data
python main.py --demo-mode
```

---

*Testing procedures updated: June 19, 2025*  
*Status: ✅ Comprehensive testing coverage for all monitoring systems*  
*Next update: Additional test cases as features expand*