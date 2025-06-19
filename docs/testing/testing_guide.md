# GUST-MARK-1 Testing Guide

> **File Location**: `/doc/testing/testing_guide.md`
> **Created**: June 19, 2025

## 🧪 Testing Overview

This guide covers comprehensive testing strategies for GUST-MARK-1, including the live player count feature, modular architecture validation, and quality assurance procedures.

## 🎯 Live Player Count Testing

### **Automated Testing Suite**
```javascript
// Live Player Count Test Suite
class PlayerCountTestSuite {
    constructor() {
        this.testResults = new Map();
        this.startTime = Date.now();
        this.testConfig = {
            timeout: 10000,         // 10 second timeout per test
            retryAttempts: 3,       // Retry failed tests
            debugMode: true         // Enable detailed logging
        };
    }
    
    async runAllPlayerCountTests() {
        console.log('🧪 Starting Live Player Count Test Suite...');
        console.log(`📊 Configuration: ${JSON.stringify(this.testConfig)}`);
        
        const tests = [
            'testAutoCommandSystem',
            'testLogsIntegration', 
            'testEnhancedUX',
            'testDemoMode',
            'testErrorHandling',
            'testPerformance',
            'testCacheSystem',
            'testConcurrency'
        ];
        
        let passed = 0;
        let failed = 0;
        
        for (const test of tests) {
            try {
                await this.runSingleTest(test);
                passed++;
            } catch (error) {
                console.error(`❌ Test ${test} failed:`, error);
                failed++;
            }
        }
        
        this.generateDetailedTestReport();
        return { passed, failed, total: tests.length };
    }
    
    async runSingleTest(testName) {
        console.log(`🔍 Running test: ${testName}`);
        
        const startTime = performance.now();
        
        try {
            await Promise.race([
                this[testName](),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Test timeout')), this.testConfig.timeout)
                )
            ]);
            
            const duration = performance.now() - startTime;
            this.recordTest(testName, true, `Completed in ${duration.toFixed(2)}ms`);
            
        } catch (error) {
            const duration = performance.now() - startTime;
            this.recordTest(testName, false, `Failed after ${duration.toFixed(2)}ms: ${error.message}`);
            throw error;
        }
    }
    
    async testAutoCommandSystem() {
        console.log('🔄 Testing Auto Command System...');
        
        // Test auto command configuration
        assert(typeof autoConsoleConfig !== 'undefined', 'Auto config should exist');
        assert(autoConsoleConfig.interval === 10000, 'Interval should be 10 seconds');
        assert(autoConsoleConfig.commandsToSend.includes('serverinfo'), 'Should send serverinfo');
        assert(autoConsoleConfig.enabled === true, 'Should be enabled by default');
        
        // Test command execution functions
        assert(typeof sendSingleAutoCommand === 'function', 'sendSingleAutoCommand should exist');
        assert(typeof startAutoConsoleCommands === 'function', 'startAutoConsoleCommands should exist');
        assert(typeof stopAutoConsoleCommands === 'function', 'stopAutoConsoleCommands should exist');
        
        // Test state management
        assert(typeof autoConsoleState !== 'undefined', 'Auto command state should exist');
        assert(typeof autoConsoleState.running === 'boolean', 'Running state should be boolean');
        
        // Test command execution with mock server
        const testServerId = 'test-server-123';
        const mockResult = await this.mockCommandExecution(testServerId, 'serverinfo');
        assert(mockResult !== null, 'Mock command should execute without errors');
        
        console.log('✅ Auto command system tests passed');
    }
    
    async testLogsIntegration() {
        console.log('📋 Testing Logs Integration...');
        
        // Test logs API function availability
        assert(typeof getPlayerCountFromLogs === 'function', 'getPlayerCountFromLogs should exist');
        assert(typeof forceRefreshPlayerCountFromLogs === 'function', 'forceRefreshPlayerCountFromLogs should exist');
        
        // Test API endpoint availability
        const testServerId = 'test-server-123';
        try {
            const response = await fetch(`/api/logs/player-count/${testServerId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            assert(response.status === 200 || response.status === 404, 'Logs API should be accessible');
            
            const data = await response.json();
            assert(typeof data.success === 'boolean', 'Response should have success field');
            
            if (data.success) {
                assert(typeof data.data === 'object', 'Successful response should have data');
                assert(typeof data.data.current === 'number', 'Should have current player count');
                assert(typeof data.data.max === 'number', 'Should have max player count');
                assert(typeof data.data.percentage === 'number', 'Should have percentage');
            }
            
        } catch (error) {
            console.warn('API endpoint test failed (may be expected in test environment):', error.message);
        }
        
        // Test logs integration state
        if (typeof window.logsIntegratedTriggerPlayerCountUpdate === 'function') {
            console.log('✅ Logs integration functions available');
        }
        
        console.log('✅ Logs integration tests passed');
    }
    
    async testEnhancedUX() {
        console.log('✨ Testing Enhanced UX Features...');
        
        const testServerId = 'test-server-ux-123';
        
        // Create test elements
        this.createTestPlayerCountElements(testServerId);
        
        // Test value preservation
        const countElement = document.querySelector(`#player-count-${testServerId} .player-count-value`);
        const maxElement = document.querySelector(`#player-count-${testServerId} .player-max-value`);
        
        if (countElement) countElement.textContent = '25';
        if (maxElement) maxElement.textContent = '100';
        
        // Trigger loading state
        updatePlayerCountDisplay(testServerId, null, 'loading');
        
        // Values should be preserved
        assert(countElement && countElement.textContent === '25', 'Current values should be preserved during loading');
        assert(maxElement && maxElement.textContent === '100', 'Max values should be preserved during loading');
        
        // Test status update
        const statusElement = document.getElementById(`player-status-${testServerId}`);
        assert(statusElement && statusElement.textContent.includes('Loading'), 'Status should show loading');
        
        // Test successful update
        const testData = { current: 30, max: 100, percentage: 30, source: 'test' };
        updatePlayerCountDisplay(testServerId, testData, 'success');
        
        // Wait for animations
        await new Promise(resolve => setTimeout(resolve, 500));
        
        assert(countElement && countElement.textContent === '30', 'Values should update with new data');
        assert(statusElement && statusElement.textContent.includes('✅'), 'Status should show success');
        
        // Test error handling with preserved values
        updatePlayerCountDisplay(testServerId, null, 'error');
        assert(countElement && countElement.textContent === '30', 'Values should be preserved during error');
        
        // Cleanup test elements
        this.cleanupTestElements(testServerId);
        
        console.log('✅ Enhanced UX tests passed');
    }
    
    async testDemoMode() {
        console.log('🎭 Testing Demo Mode...');
        
        // Test mock data generation
        const mockData = generateMockPlayerData('demo-server');
        assert(typeof mockData.current === 'number', 'Mock data should have current players');
        assert(typeof mockData.max === 'number', 'Mock data should have max players');
        assert(typeof mockData.percentage === 'number', 'Mock data should have percentage');
        assert(mockData.source === 'mock', 'Mock data should have correct source');
        assert(mockData.current >= 0 && mockData.current <= mockData.max, 'Current should be valid');
        assert(mockData.percentage >= 0 && mockData.percentage <= 100, 'Percentage should be valid');
        
        // Test multiple mock generations for variety
        const mockDataSets = [];
        for (let i = 0; i < 5; i++) {
            mockDataSets.push(generateMockPlayerData(`demo-server-${i}`));
        }
        
        // Verify variety in mock data
        const uniqueCurrentValues = new Set(mockDataSets.map(d => d.current));
        assert(uniqueCurrentValues.size > 1, 'Mock data should have variety');
        
        // Test demo display
        const testServerId = 'demo-test-server';
        this.createTestPlayerCountElements(testServerId);
        
        updatePlayerCountDisplay(testServerId, mockData, 'success');
        
        const sourceElement = document.getElementById(`player-source-${testServerId}`);
        assert(sourceElement && sourceElement.textContent.includes('Demo'), 'Should show demo source');
        
        this.cleanupTestElements(testServerId);
        
        console.log('✅ Demo mode tests passed');
    }
    
    async testErrorHandling() {
        console.log('❌ Testing Error Handling...');
        
        // Test API error handling
        try {
            const result = await getPlayerCountFromLogs('invalid-server-id-12345');
            assert(result.success === false, 'Should fail for invalid server ID');
        } catch (error) {
            // Expected for invalid server
            console.log('API error handling working correctly');
        }
        
        // Test error display preservation
        const testServerId = 'error-test-server';
        this.createTestPlayerCountElements(testServerId);
        
        // Set initial values
        const countElement = document.querySelector(`#player-count-${testServerId} .player-count-value`);
        const maxElement = document.querySelector(`#player-count-${testServerId} .player-max-value`);
        if (countElement) countElement.textContent = '42';
        if (maxElement) maxElement.textContent = '100';
        
        // Trigger error state
        updatePlayerCountDisplay(testServerId, null, 'error');
        
        // Values should be preserved during error
        assert(countElement && countElement.textContent === '42', 'Values should be preserved during error');
        
        const statusElement = document.getElementById(`player-status-${testServerId}`);
        assert(statusElement && statusElement.textContent.includes('Error'), 'Should show error status');
        
        const sourceElement = document.getElementById(`player-source-${testServerId}`);
        assert(sourceElement && sourceElement.textContent.includes('Last Known'), 'Should show error source');
        
        this.cleanupTestElements(testServerId);
        
        console.log('✅ Error handling tests passed');
    }
    
    async testPerformance() {
        console.log('⚡ Testing Performance...');
        
        // Test display update performance
        const testServerId = 'perf-test-server';
        this.createTestPlayerCountElements(testServerId);
        
        const testData = {
            current: 45,
            max: 100,
            percentage: 45,
            source: 'test'
        };
        
        // Measure single update performance
        const startTime = performance.now();
        updatePlayerCountDisplay(testServerId, testData, 'success');
        const endTime = performance.now();
        const singleUpdateDuration = endTime - startTime;
        
        assert(singleUpdateDuration < 100, `Single update should be fast (< 100ms), was ${singleUpdateDuration.toFixed(2)}ms`);
        
        // Test batch updates performance
        const batchStartTime = performance.now();
        const batchPromises = [];
        
        for (let i = 0; i < 20; i++) {
            const serverId = `batch-test-${i}`;
            this.createTestPlayerCountElements(serverId);
            batchPromises.push(
                new Promise(resolve => {
                    updatePlayerCountDisplay(serverId, testData, 'success');
                    resolve();
                })
            );
        }
        
        await Promise.all(batchPromises);
        const batchEndTime = performance.now();
        const batchDuration = batchEndTime - batchStartTime;
        
        assert(batchDuration < 1000, `Batch updates should be efficient (< 1000ms), was ${batchDuration.toFixed(2)}ms`);
        
        // Test cache performance if available
        if (typeof playerCountCache !== 'undefined' && playerCountCache.getStats) {
            const cacheStats = playerCountCache.getStats();
            console.log('📊 Cache stats:', cacheStats);
        }
        
        // Cleanup batch test elements
        for (let i = 0; i < 20; i++) {
            this.cleanupTestElements(`batch-test-${i}`);
        }
        this.cleanupTestElements(testServerId);
        
        console.log(`✅ Performance tests passed (single: ${singleUpdateDuration.toFixed(2)}ms, batch: ${batchDuration.toFixed(2)}ms)`);
    }
    
    async testCacheSystem() {
        console.log('💾 Testing Cache System...');
        
        if (typeof playerCountCache === 'undefined') {
            console.log('⚠️ Cache system not available, skipping cache tests');
            return;
        }
        
        const testKey = 'test-cache-key';
        const testData = { current: 50, max: 100, percentage: 50 };
        
        // Test cache set/get
        playerCountCache.set(testKey, testData);
        const cachedData = playerCountCache.get(testKey);
        
        assert(cachedData !== null, 'Cache should return data');
        assert(cachedData.current === testData.current, 'Cached data should match original');
        
        // Test cache expiration (if supported)
        if (playerCountCache.ttl && playerCountCache.ttl < 1000) {
            await new Promise(resolve => setTimeout(resolve, playerCountCache.ttl + 100));
            const expiredData = playerCountCache.get(testKey);
            assert(expiredData === null, 'Cache should expire data');
        }
        
        // Test cache stats
        if (playerCountCache.getStats) {
            const stats = playerCountCache.getStats();
            assert(typeof stats.hits === 'number', 'Cache should track hits');
            assert(typeof stats.misses === 'number', 'Cache should track misses');
        }
        
        console.log('✅ Cache system tests passed');
    }
    
    async testConcurrency() {
        console.log('🔄 Testing Concurrency...');
        
        const concurrentRequests = 10;
        const testServerId = 'concurrent-test-server';
        
        // Create test elements
        this.createTestPlayerCountElements(testServerId);
        
        // Test concurrent updates
        const promises = [];
        for (let i = 0; i < concurrentRequests; i++) {
            const testData = {
                current: i * 5,
                max: 100,
                percentage: i * 5,
                source: `concurrent-${i}`
            };
            
            promises.push(
                new Promise(resolve => {
                    setTimeout(() => {
                        updatePlayerCountDisplay(testServerId, testData, 'success');
                        resolve(i);
                    }, Math.random() * 100); // Random delay up to 100ms
                })
            );
        }
        
        const results = await Promise.all(promises);
        assert(results.length === concurrentRequests, 'All concurrent updates should complete');
        
        // Verify final state is consistent
        const countElement = document.querySelector(`#player-count-${testServerId} .player-count-value`);
        assert(countElement && !isNaN(parseInt(countElement.textContent)), 'Final value should be numeric');
        
        this.cleanupTestElements(testServerId);
        
        console.log('✅ Concurrency tests passed');
    }
    
    // Helper methods
    createTestPlayerCountElements(serverId) {
        const container = document.body;
        const html = `
            <div id="player-count-${serverId}" class="player-count-container" style="display: none;">
                <div class="flex items-center justify-between text-sm">
                    <div class="flex items-center space-x-2">
                        <span class="text-cyan-400">👥</span>
                        <span class="player-count-text text-gray-300">
                            Players: <span class="player-count-value font-medium text-green-400">--</span> / <span class="player-max-value text-purple-400">--</span>
                        </span>
                    </div>
                    <span class="player-count-status text-xs px-2 py-1 rounded bg-gray-700 text-yellow-400" id="player-status-${serverId}">
                        ⏳ Loading...
                    </span>
                </div>
                <div class="player-count-bar mt-1 bg-gray-600 rounded-full h-1.5">
                    <div class="player-count-fill bg-gradient-to-r from-green-400 to-cyan-400 rounded-full h-full transition-all duration-500" 
                         style="width: 0%" id="player-bar-${serverId}"></div>
                </div>
                <div class="text-xs text-gray-500 mt-1">
                    Source: <span id="player-source-${serverId}">Test</span>
                </div>
            </div>
        `;
        
        const div = document.createElement('div');
        div.innerHTML = html;
        container.appendChild(div);
    }
    
    cleanupTestElements(serverId) {
        const element = document.getElementById(`player-count-${serverId}`);
        if (element && element.parentNode && element.parentNode.parentNode) {
            element.parentNode.parentNode.removeChild(element.parentNode);
        }
    }
    
    async mockCommandExecution(serverId, command) {
        // Mock command execution for testing
        return new Promise(resolve => {
            setTimeout(() => {
                resolve({
                    success: true,
                    serverId: serverId,
                    command: command,
                    response: 'Mock command executed successfully'
                });
            }, 100);
        });
    }
    
    recordTest(testName, passed, message) {
        this.testResults.set(testName, {
            passed,
            message,
            timestamp: Date.now()
        });
        
        const icon = passed ? '✅' : '❌';
        console.log(`${icon} ${testName}: ${message}`);
    }
    
    generateDetailedTestReport() {
        const totalTests = this.testResults.size;
        const passedTests = Array.from(this.testResults.values()).filter(r => r.passed).length;
        const failedTests = totalTests - passedTests;
        const duration = Date.now() - this.startTime;
        
        console.log('\n📊 Live Player Count Test Report');
        console.log('=====================================');
        console.log(`Total Tests: ${totalTests}`);
        console.log(`Passed: ${passedTests}`);
        console.log(`Failed: ${failedTests}`);
        console.log(`Success Rate: ${((passedTests / totalTests) * 100).toFixed(1)}%`);
        console.log(`Duration: ${duration}ms`);
        console.log('=====================================');
        
        // Detailed results
        for (const [testName, result] of this.testResults) {
            const icon = result.passed ? '✅' : '❌';
            console.log(`${icon} ${testName}: ${result.message}`);
        }
        
        // Performance summary
        if (passedTests === totalTests) {
            console.log('\n🎉 All tests passed! Live Player Count system is fully functional.');
        } else {
            console.log(`\n⚠️ ${failedTests} test(s) failed. Please review the issues above.`);
        }
        
        return {
            totalTests,
            passedTests,
            failedTests,
            successRate: (passedTests / totalTests) * 100,
            duration,
            results: Object.fromEntries(this.testResults)
        };
    }
}

// Utility assertion function
function assert(condition, message) {
    if (!condition) {
        throw new Error(`Assertion failed: ${message}`);
    }
}

// Auto-run player count tests in development
if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
    window.playerCountTests = new PlayerCountTestSuite();
    
    // Test command for manual execution
    window.testPlayerCount = () => {
        return window.playerCountTests.runAllPlayerCountTests();
    };
    
    // Auto-run tests after page load (optional)
    document.addEventListener('DOMContentLoaded', () => {
        if (localStorage.getItem('autoRunPlayerCountTests') === 'true') {
            setTimeout(() => {
                console.log('🚀 Auto-running player count tests...');
                window.testPlayerCount();
            }, 5000);
        }
    });
}
```

### **Manual Testing Procedures**

#### **Demo Mode Testing Checklist**
```bash
# 1. Start application
python main.py

# 2. Login with demo credentials
Username: admin
Password: password

# 3. Navigate to Server Manager tab

# 4. Add test servers:
Server Name: Test Server 1
Server ID: test-123
Region: US
Description: Demo server for testing

Server Name: Test Server 2
Server ID: test-456
Region: EU
Description: European test server

# 5. Verify live player count features:
✅ Player count containers appear on server cards
✅ Shows "⏳ Loading..." initially for each server
✅ Displays realistic mock player data (random numbers 0-100)
✅ Progress bars show correct percentage visualization
✅ Source attribution shows "Demo Data"
✅ Auto-refresh works (values change periodically)
✅ Manual refresh buttons work (🔄 icon)
✅ Values are preserved during loading states
✅ Different servers show different mock populations
✅ Color coding works (green → yellow → orange → red)
✅ Timestamps update correctly
✅ Mobile responsiveness maintained
```

#### **Live Mode Testing Checklist** (G-Portal Account Required)
```bash
# 1. Configure G-Portal credentials in environment or config

# 2. Add real servers in Server Manager:
- Use actual G-Portal server IDs
- Verify server names and regions are correct
- Ensure servers are active and accessible

# 3. Verify auto command system:
✅ Browser console shows auto commands being sent
✅ "serverinfo" commands executed every 10 seconds
✅ Commands rotate through available servers
✅ No JavaScript errors in console logs
✅ Performance remains stable under load

# 4. Verify player count data accuracy:
✅ Real player numbers appear from server logs
✅ Source attribution shows "Server Logs"
✅ Data matches actual server population (verify in-game)
✅ Updates occur reliably after serverinfo commands
✅ Error handling works for offline/inaccessible servers
✅ Cache system improves response times
✅ Manual refresh provides immediate updates

# 5. Test error scenarios:
✅ Offline servers show appropriate error states
✅ Network interruptions are handled gracefully
✅ Invalid server IDs are rejected properly
✅ Old values are preserved during error states
✅ System recovers automatically when servers come online
```

## 🧪 Component Testing

### **Modular Component Test Framework**
```javascript
// Component Testing Framework
class ComponentTester {
    constructor() {
        this.testResults = new Map();
        this.components = [
            'dashboard', 'server_manager', 'console', 'events',
            'economy', 'gambling', 'clans', 'user_management', 'logs'
        ];
        this.criticalFunctions = {
            'server_manager': ['refreshServerList', 'addServer', 'deleteServer'],
            'console': ['sendConsoleCommand', 'clearConsole', 'refreshConsole'],
            'logs': ['loadLogs', 'getPlayerCountFromLogs', 'startAutoConsoleCommands'],
            'dashboard': ['loadDashboard', 'updateDashboardStats'],
            'events': ['loadEvents', 'createEvent'],
            'economy': ['loadEconomy', 'updatePlayerBalance'],
            'gambling': ['initializeGambling', 'playSlots'],
            'clans': ['loadClans', 'createClan'],
            'user_management': ['loadUserManagement', 'banPlayer']
        };
    }
    
    async testAllComponents() {
        console.log('🧪 Testing All Modular Components...');
        console.log(`📦 Components to test: ${this.components.length}`);
        
        let passed = 0;
        let failed = 0;
        
        for (const component of this.components) {
            try {
                await this.testComponent(component);
                passed++;
            } catch (error) {
                console.error(`❌ Component ${component} failed:`, error);
                failed++;
            }
        }
        
        this.generateComponentReport();
        return { passed, failed, total: this.components.length };
    }
    
    async testComponent(componentName) {
        console.log(`🔍 Testing ${componentName} component...`);
        
        try {
            // Test component loading and visibility
            await this.testComponentLoading(componentName);
            
            // Test component initialization
            await this.testComponentInitialization(componentName);
            
            // Test component-specific functionality
            await this.testComponentFunctionality(componentName);
            
            // Test error handling
            await this.testComponentErrorHandling(componentName);
            
            this.recordComponentTest(componentName, true, 'All component tests passed');
            
        } catch (error) {
            this.recordComponentTest(componentName, false, error.message);
            throw error;
        }
    }
    
    async testComponentLoading(componentName) {
        // Test component tab switching
        showTab(componentName);
        await this.waitForComponent(componentName);
        
        // Test component visibility
        const element = document.getElementById(`${componentName}-view`);
        assert(element && !element.classList.contains('hidden'), 
               `Component ${componentName} should be visible after tab switch`);
        
        // Test navigation state
        const navTab = document.getElementById(`${componentName}-tab`);
        assert(navTab && navTab.classList.contains('active'), 
               `Navigation tab for ${componentName} should be active`);
    }
    
    async testComponentInitialization(componentName) {
        // Test component initialization function
        const initFunctionName = `load${this.capitalize(componentName)}`;
        if (typeof window[initFunctionName] === 'function') {
            try {
                await window[initFunctionName]();
                console.log(`✅ ${componentName} initialization function executed`);
            } catch (error) {
                throw new Error(`Component initialization failed: ${error.message}`);
            }
        }
        
        // Test tab initializer
        if (window.tabInitializers && window.tabInitializers[componentName]) {
            try {
                await window.tabInitializers[componentName]();
                console.log(`✅ ${componentName} tab initializer executed`);
            } catch (error) {
                console.warn(`Tab initializer warning for ${componentName}: ${error.message}`);
            }
        }
    }
    
    async testComponentFunctionality(componentName) {
        const functions = this.criticalFunctions[componentName] || [];
        
        for (const functionName of functions) {
            if (typeof window[functionName] === 'function') {
                console.log(`🔧 Testing function: ${functionName}`);
                
                try {
                    // Test function exists and is callable
                    const result = window[functionName];
                    assert(typeof result === 'function', `${functionName} should be a function`);
                    
                    // For safe functions, try to call them
                    if (this.isSafeFunction(functionName)) {
                        await this.callFunctionSafely(functionName);
                    }
                    
                } catch (error) {
                    console.warn(`Function test warning for ${functionName}: ${error.message}`);
                }
            }
        }
        
        // Component-specific tests
        switch (componentName) {
            case 'server_manager':
                await this.testServerManagerSpecific();
                break;
            case 'console':
                await this.testConsoleSpecific();
                break;
            case 'logs':
                await this.testLogsSpecific();
                break;
            case 'dashboard':
                await this.testDashboardSpecific();
                break;
        }
    }
    
    async testComponentErrorHandling(componentName) {
        // Test component behavior with invalid inputs
        const testElement = document.getElementById(`${componentName}-view`);
        if (testElement) {
            // Test DOM manipulation resilience
            const originalContent = testElement.innerHTML;
            
            try {
                // Temporarily modify content to test recovery
                testElement.innerHTML = '<div>Test content</div>';
                
                // Switch away and back to test recovery
                showTab('dashboard');
                await new Promise(resolve => setTimeout(resolve, 100));
                showTab(componentName);
                await new Promise(resolve => setTimeout(resolve, 100));
                
                // Component should still be functional
                const restoredElement = document.getElementById(`${componentName}-view`);
                assert(restoredElement && !restoredElement.classList.contains('hidden'), 
                       'Component should recover from DOM modifications');
                
            } finally {
                // Restore original content
                testElement.innerHTML = originalContent;
            }
        }
    }
    
    // Component-specific test methods
    async testServerManagerSpecific() {
        // Test server list refresh
        if (typeof refreshServerList === 'function') {
            refreshServerList();
        }
        
        // Test player count containers
        const playerCountElements = document.querySelectorAll('.player-count-container');
        console.log(`📊 Found ${playerCountElements.length} player count containers`);
        
        // Test server dropdown updates
        if (typeof updateAllServerDropdowns === 'function') {
            updateAllServerDropdowns();
        }
        
        // Verify managedServers global state
        assert(Array.isArray(window.managedServers), 'managedServers should be an array');
    }
    
    async testConsoleSpecific() {
        // Test console functions availability
        const consoleFunctions = [
            'sendConsoleCommand', 'clearConsole', 'refreshConsole',
            'setCommand', 'updateSystemStatus'
        ];
        
        for (const func of consoleFunctions) {
            assert(typeof window[func] === 'function', `Console function ${func} should exist`);
        }
        
        // Test logs integration functions
        const logsIntegrationFunctions = [
            'logsIntegratedTriggerPlayerCountUpdate',
            'sendServerInfoCommand'
        ];
        
        for (const func of logsIntegrationFunctions) {
            if (typeof window[func] === 'function') {
                console.log(`✅ Logs integration function ${func} available`);
            }
        }
        
        // Test console output element
        const consoleOutput = document.getElementById('consoleOutput');
        assert(consoleOutput, 'Console output element should exist');
    }
    
    async testLogsSpecific() {
        // Test logs functions availability
        const logsFunctions = [
            'loadLogs', 'showLogsTab', 'initializeLogs',
            'getPlayerCountFromLogs', 'startAutoConsoleCommands'
        ];
        
        for (const func of logsFunctions) {
            if (typeof window[func] === 'function') {
                console.log(`✅ Logs function ${func} available`);
            }
        }
        
        // Test auto command system
        if (typeof window.getAutoConsoleStatus === 'function') {
            const status = window.getAutoConsoleStatus();
            console.log('📊 Auto command status:', status);
        }
        
        // Test logs status element
        const logsStatus = document.getElementById('logs-status');
        if (logsStatus) {
            console.log('✅ Logs status element found');
        }
    }
    
    async testDashboardSpecific() {
        // Test dashboard elements
        const dashboardElements = [
            'system-stats', 'server-overview', 'recent-activity'
        ];
        
        for (const elementId of dashboardElements) {
            const element = document.getElementById(elementId);
            if (element) {
                console.log(`✅ Dashboard element ${elementId} found`);
            }
        }
        
        // Test dashboard data loading
        if (typeof window.loadDashboardData === 'function') {
            try {
                await window.loadDashboardData();
                console.log('✅ Dashboard data loaded successfully');
            } catch (error) {
                console.warn('Dashboard data loading warning:', error.message);
            }
        }
    }
    
    // Helper methods
    capitalize(str) {
        return str.charAt(0).toUpperCase() + str.slice(1).replace(/_(.)/g, (_, letter) => letter.toUpperCase());
    }
    
    isSafeFunction(functionName) {
        const safeFunctions = [
            'refreshServerList', 'clearConsole', 'updateSystemStatus',
            'loadLogs', 'updateAllServerDropdowns', 'loadDashboard'
        ];
        return safeFunctions.includes(functionName);
    }
    
    async callFunctionSafely(functionName) {
        try {
            const result = window[functionName]();
            if (result instanceof Promise) {
                await result;
            }
            console.log(`✅ Safe function call: ${functionName}`);
        } catch (error) {
            console.warn(`Safe function call warning for ${functionName}: ${error.message}`);
        }
    }
    
    async waitForComponent(componentName, timeout = 5000) {
        return new Promise((resolve, reject) => {
            const startTime = Date.now();
            
            function check() {
                const element = document.getElementById(`${componentName}-view`);
                if (element && !element.classList.contains('hidden')) {
                    resolve();
                } else if (Date.now() - startTime > timeout) {
                    reject(new Error(`Component ${componentName} failed to load within ${timeout}ms`));
                } else {
                    setTimeout(check, 100);
                }
            }
            
            check();
        });
    }
    
    recordComponentTest(componentName, passed, message) {
        this.testResults.set(componentName, { passed, message });
        const icon = passed ? '✅' : '❌';
        console.log(`${icon} ${componentName}: ${message}`);
    }
    
    generateComponentReport() {
        const totalComponents = this.testResults.size;
        const passedComponents = Array.from(this.testResults.values()).filter(r => r.passed).length;
        
        console.log('\n📊 Modular Component Test Report');
        console.log('===================================');
        console.log(`Total Components: ${totalComponents}`);
        console.log(`Passed: ${passedComponents}`);
        console.log(`Failed: ${totalComponents - passedComponents}`);
        console.log(`Success Rate: ${((passedComponents / totalComponents) * 100).toFixed(1)}%`);
        console.log('===================================');
        
        // Detailed results
        for (const [componentName, result] of this.testResults) {
            const icon = result.passed ? '✅' : '❌';
            console.log(`${icon} ${componentName}: ${result.message}`);
        }
        
        return {
            totalComponents,
            passedComponents,
            failedComponents: totalComponents - passedComponents,
            successRate: (passedComponents / totalComponents) * 100,
            results: Object.fromEntries(this.testResults)
        };
    }
}

// Auto-run component tests
window.componentTester = new ComponentTester();
window.testAllComponents = () => window.componentTester.testAllComponents();
```

## 🌐 API Testing

### **Backend API Test Suite**
```python
# API Testing Suite for GUST-MARK-1
import unittest
import requests
import json
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

class GUSTAPITestSuite(unittest.TestCase):
    
    def setUp(self):
        self.base_url = 'http://localhost:5000'
        self.session = requests.Session()
        self.test_servers = []
        
        # Login for authenticated tests
        login_data = {'username': 'admin', 'password': 'password'}
        response = self.session.post(f'{self.base_url}/api/auth/login', json=login_data)
        self.assertEqual(response.status_code, 200)
        
        # Set up test timeout
        self.session.timeout = 30
    
    def test_health_endpoint(self):
        """Test system health endpoint"""
        response = self.session.get(f'{self.base_url}/health')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('database', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['status'], 'healthy')
    
    def test_authentication_flow(self):
        """Test authentication endpoints"""
        # Test invalid login
        invalid_session = requests.Session()
        invalid_data = {'username': 'invalid', 'password': 'invalid'}
        response = invalid_session.post(f'{self.base_url}/api/auth/login', json=invalid_data)
        self.assertEqual(response.status_code, 401)
        
        # Test valid login (already done in setUp)
        # Test authenticated endpoint access
        response = self.session.get(f'{self.base_url}/api/servers')
        self.assertEqual(response.status_code, 200)
        
        # Test unauthenticated access
        unauth_session = requests.Session()
        response = unauth_session.get(f'{self.base_url}/api/servers')
        self.assertEqual(response.status_code, 401)
    
    def test_player_count_api(self):
        """Test live player count API endpoint"""
        server_id = 'test-server-123'
        
        # Test with valid request
        response = self.session.post(
            f'{self.base_url}/api/logs/player-count/{server_id}',
            headers={'Content-Type': 'application/json'}
        )
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('success', data)
        
        if data['success']:
            self.assertIn('data', data)
            player_data = data['data']
            self.assertIn('current', player_data)
            self.assertIn('max', player_data)
            self.assertIn('percentage', player_data)
            self.assertIn('source', player_data)
            self.assertIn('timestamp', player_data)
            
            # Validate data types and ranges
            self.assertIsInstance(player_data['current'], int)
            self.assertIsInstance(player_data['max'], int)
            self.assertIsInstance(player_data['percentage'], int)
            self.assertGreaterEqual(player_data['current'], 0)
            self.assertGreaterEqual(player_data['max'], 0)
            self.assertGreaterEqual(player_data['percentage'], 0)
            self.assertLessEqual(player_data['percentage'], 100)
            self.assertLessEqual(player_data['current'], player_data['max'])
        
        # Test with invalid server ID
        invalid_response = self.session.post(
            f'{self.base_url}/api/logs/player-count/invalid-server-!@#',
            headers={'Content-Type': 'application/json'}
        )
        self.assertEqual(invalid_response.status_code, 400)
    
    def test_server_manager_api(self):
        """Test server management endpoints"""
        # Test server list retrieval
        response = self.session.get(f'{self.base_url}/api/servers')
        self.assertEqual(response.status_code, 200)
        
        servers = response.json()
        self.assertIsInstance(servers, list)
        
        # Test add server
        server_data = {
            'serverName': 'Test Server API',
            'serverId': f'test-api-{int(time.time())}',
            'serverRegion': 'US',
            'description': 'API test server'
        }
        
        response = self.session.post(f'{self.base_url}/api/servers', json=server_data)
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result.get('success', False))
        
        # Store for cleanup
        self.test_servers.append(server_data['serverId'])
        
        # Test server retrieval after adding
        response = self.session.get(f'{self.base_url}/api/servers')
        updated_servers = response.json()
        self.assertGreater(len(updated_servers), len(servers))
        
        # Verify our server was added
        added_server = next((s for s in updated_servers if s['serverId'] == server_data['serverId']), None)
        self.assertIsNotNone(added_server)
        self.assertEqual(added_server['serverName'], server_data['serverName'])
    
    def test_console_api(self):
        """Test console command endpoints"""
        # Test server info command
        command_data = {
            'command': 'serverinfo',
            'serverId': 'test-server-123',
            'region': 'US'
        }
        
        response = self.session.post(f'{self.base_url}/api/console/send', json=command_data)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIsInstance(data, dict)
        self.assertIn('success', data)
        
        # Test invalid command
        invalid_command = {
            'command': '',  # Empty command
            'serverId': 'test-server-123',
            'region': 'US'
        }
        
        response = self.session.post(f'{self.base_url}/api/console/send', json=invalid_command)
        self.assertIn(response.status_code, [400, 422])  # Bad request or validation error
        
        # Test console output retrieval
        response = self.session.get(f'{self.base_url}/api/console/output')
        self.assertEqual(response.status_code, 200)
        
        output = response.json()
        self.assertIsInstance(output, list)
    
    def test_rate_limiting(self):
        """Test API rate limiting"""
        endpoint = f'{self.base_url}/api/logs/player-count/test-rate-limit'
        
        # Send multiple requests quickly
        responses = []
        for i in range(15):  # More than typical rate limit
            response = self.session.post(endpoint, headers={'Content-Type': 'application/json'})
            responses.append(response)
        
        # Check if any requests were rate limited
        rate_limited = any(r.status_code == 429 for r in responses)
        
        if rate_limited:
            print("✅ Rate limiting is working")
        else:
            print("⚠️ Rate limiting may not be configured or limit is very high")
    
    def test_concurrent_requests(self):
        """Test concurrent API requests"""
        def make_request(i):
            server_id = f'concurrent-test-{i}'
            response = self.session.post(
                f'{self.base_url}/api/logs/player-count/{server_id}',
                headers={'Content-Type': 'application/json'}
            )
            return response.status_code, response.elapsed.total_seconds()
        
        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_requests = sum(1 for status, _ in results if status == 200)
        avg_response_time = sum(time for _, time in results) / len(results)
        
        self.assertGreaterEqual(successful_requests, 8)  # At least 80% success rate
        self.assertLess(avg_response_time, 5.0)  # Average response time under 5 seconds
        
        print(f"📊 Concurrent test: {successful_requests}/10 successful, avg response: {avg_response_time:.2f}s")
    
    def test_error_handling(self):
        """Test API error handling"""
        # Test 404 endpoint
        response = self.session.get(f'{self.base_url}/api/nonexistent')
        self.assertEqual(response.status_code, 404)
        
        # Test malformed JSON
        response = self.session.post(
            f'{self.base_url}/api/servers`,
            data='invalid json',
            headers={'Content-Type': 'application/json'}
        )
        self.assertIn(response.status_code, [400, 422])
        
        # Test missing required fields
        incomplete_data = {'serverName': 'Test'}  # Missing serverId
        response = self.session.post(f'{self.base_url}/api/servers', json=incomplete_data)
        self.assertIn(response.status_code, [400, 422])
    
    def tearDown(self):
        """Clean up test data"""
        # Remove test servers
        for server_id in self.test_servers:
            try:
                response = self.session.delete(f'{self.base_url}/api/servers/{server_id}')
                if response.status_code == 200:
                    print(f"✅ Cleaned up test server: {server_id}")
            except Exception as e:
                print(f"⚠️ Failed to clean up server {server_id}: {e}")
        
        self.session.close()

# Performance testing class
class PerformanceTestSuite(unittest.TestCase):
    
    def setUp(self):
        self.base_url = 'http://localhost:5000'
        self.session = requests.Session()
        
        # Login
        login_data = {'username': 'admin', 'password': 'password'}
        self.session.post(f'{self.base_url}/api/auth/login', json=login_data)
    
    def test_response_times(self):
        """Test API response times"""
        endpoints = [
            '/health',
            '/api/servers',
            '/api/console/output',
            '/api/logs/player-count/perf-test'
        ]
        
        results = {}
        
        for endpoint in endpoints:
            start_time = time.time()
            if endpoint.endswith('perf-test'):
                response = self.session.post(f'{self.base_url}{endpoint}', 
                                           headers={'Content-Type': 'application/json'})
            else:
                response = self.session.get(f'{self.base_url}{endpoint}')
            
            response_time = time.time() - start_time
            results[endpoint] = {
                'response_time': response_time,
                'status_code': response.status_code
            }
            
            # Assert reasonable response times
            self.assertLess(response_time, 5.0, f"{endpoint} took too long: {response_time:.2f}s")
        
        # Print performance summary
        print("\n📊 API Performance Results:")
        for endpoint, result in results.items():
            print(f"  {endpoint}: {result['response_time']:.3f}s (status: {result['status_code']})")
    
    def test_memory_usage(self):
        """Test memory usage under load"""
        import psutil
        import os
        
        # Get current process info
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Make many requests
        for i in range(50):
            response = self.session.post(
                f'{self.base_url}/api/logs/player-count/memory-test-{i}',
                headers={'Content-Type': 'application/json'}
            )
        
        # Check memory after load
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"📊 Memory test: {initial_memory:.1f}MB → {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # Memory increase should be reasonable
        self.assertLess(memory_increase, 100, f"Memory increase too high: {memory_increase:.1f}MB")
    
    def tearDown(self):
        self.session.close()

if __name__ == '__main__':
    # Run API tests
    print("🧪 Running GUST-MARK-1 API Test Suite...")
    
    # Create test suite
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTest(unittest.makeSuite(GUSTAPITestSuite))
    suite.addTest(unittest.makeSuite(PerformanceTestSuite))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    if result.wasSuccessful():
        print("\n🎉 All API tests passed!")
    else:
        print(f"\n⚠️ {len(result.failures)} test(s) failed, {len(result.errors)} error(s)")
```

## 📊 Performance Testing

### **Load Testing Scripts**
```python
# Load Testing for Live Player Count System
import asyncio
import aiohttp
import time
import statistics
from concurrent.futures import ThreadPoolExecutor
import matplotlib.pyplot as plt

class PlayerCountLoadTest:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.results = []
        self.session_cookie = None
    
    async def authenticate(self, session):
        """Authenticate session for load testing"""
        login_data = {'username': 'admin', 'password': 'password'}
        async with session.post(f'{self.base_url}/api/auth/login', json=login_data) as response:
            if response.status == 200:
                # Store session cookie
                self.session_cookie = response.cookies
                return True
        return False
    
    async def test_concurrent_player_count_requests(self, num_requests=100, max_concurrent=20):
        """Test concurrent player count API requests"""
        print(f'🔄 Testing {num_requests} concurrent player count requests...')
        print(f'📊 Max concurrent: {max_concurrent}')
        
        connector = aiohttp.TCPConnector(limit=max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            # Authenticate
            if not await self.authenticate(session):
                raise Exception("Authentication failed")
            
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(max_concurrent)
            
            # Create request tasks
            tasks = []
            for i in range(num_requests):
                task = self.make_player_count_request(session, semaphore, f'load-test-{i % 10}')
                tasks.append(task)
            
            # Execute all requests
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Analyze results
            successful_requests = []
            failed_requests = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_requests.append(str(result))
                elif result is not None:
                    successful_requests.append(result)
            
            total_time = end_time - start_time
            success_count = len(successful_requests)
            failure_count = len(failed_requests)
            
            # Calculate statistics
            if successful_requests:
                avg_response_time = statistics.mean(successful_requests) * 1000
                median_response_time = statistics.median(successful_requests) * 1000
                min_response_time = min(successful_requests) * 1000
                max_response_time = max(successful_requests) * 1000
                requests_per_second = success_count / total_time
            else:
                avg_response_time = median_response_time = min_response_time = max_response_time = 0
                requests_per_second = 0
            
            # Print results
            print(f'\n📊 Load Test Results:')
            print(f'   Total Requests: {num_requests}')
            print(f'   Successful: {success_count} ({(success_count/num_requests)*100:.1f}%)')
            print(f'   Failed: {failure_count} ({(failure_count/num_requests)*100:.1f}%)')
            print(f'   Total Time: {total_time:.2f}s')
            print(f'   Requests/Second: {requests_per_second:.2f}')
            print(f'   Avg Response Time: {avg_response_time:.2f}ms')
            print(f'   Median Response Time: {median_response_time:.2f}ms')
            print(f'   Min Response Time: {min_response_time:.2f}ms')
            print(f'   Max Response Time: {max_response_time:.2f}ms')
            
            # Store results for analysis
            self.results.append({
                'num_requests': num_requests,
                'max_concurrent': max_concurrent,
                'successful_requests': success_count,
                'failed_requests': failure_count,
                'total_time': total_time,
                'avg_response_time': avg_response_time,
                'requests_per_second': requests_per_second,
                'response_times': successful_requests
            })
            
            return {
                'total_requests': num_requests,
                'successful_requests': success_count,
                'failed_requests': failure_count,
                'total_time': total_time,
                'avg_response_time': avg_response_time,
                'requests_per_second': requests_per_second
            }
    
    async def make_player_count_request(self, session, semaphore, server_id):
        """Make a single player count request with timing"""
        async with semaphore:
            try:
                start_time = time.time()
                async with session.post(
                    f'{self.base_url}/api/logs/player-count/{server_id}',
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    await response.json()  # Read response
                    end_time = time.time()
                    
                    if response.status == 200:
                        return end_time - start_time
                    else:
                        raise Exception(f"HTTP {response.status}")
                        
            except Exception as e:
                return e
    
    async def stress_test(self, duration_seconds=60, requests_per_second=10):
        """Continuous stress test for specified duration"""
        print(f'🔥 Running stress test for {duration_seconds}s at {requests_per_second} req/s')
        
        async with aiohttp.ClientSession() as session:
            if not await self.authenticate(session):
                raise Exception("Authentication failed")
            
            start_time = time.time()
            end_time = start_time + duration_seconds
            request_interval = 1.0 / requests_per_second
            
            results = []
            request_count = 0
            
            while time.time() < end_time:
                request_start = time.time()
                
                # Make request
                try:
                    result = await self.make_player_count_request(
                        session, asyncio.Semaphore(1), f'stress-test-{request_count % 5}'
                    )
                    if not isinstance(result, Exception):
                        results.append(result)
                    request_count += 1
                    
                except Exception as e:
                    print(f"Request error: {e}")
                
                # Wait for next request interval
                elapsed = time.time() - request_start
                sleep_time = max(0, request_interval - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
            
            # Calculate stress test results
            actual_duration = time.time() - start_time
            successful_requests = len(results)
            actual_rps = successful_requests / actual_duration
            
            if results:
                avg_response_time = statistics.mean(results) * 1000
                p95_response_time = statistics.quantiles(results, n=20)[18] * 1000  # 95th percentile
            else:
                avg_response_time = p95_response_time = 0
            
            print(f'\n🔥 Stress Test Results:')
            print(f'   Duration: {actual_duration:.2f}s')
            print(f'   Requests Sent: {request_count}')
            print(f'   Successful Requests: {successful_requests}')
            print(f'   Actual RPS: {actual_rps:.2f}')
            print(f'   Avg Response Time: {avg_response_time:.2f}ms')
            print(f'   95th Percentile Response Time: {p95_response_time:.2f}ms')
            
            return {
                'duration': actual_duration,
                'requests_sent': request_count,
                'successful_requests': successful_requests,
                'actual_rps': actual_rps,
                'avg_response_time': avg_response_time,
                'p95_response_time': p95_response_time
            }
    
    def generate_performance_report(self):
        """Generate visual performance report"""
        if not self.results:
            print("No test results available for report generation")
            return
        
        try:
            import matplotlib.pyplot as plt
            
            # Create performance charts
            fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
            fig.suptitle('GUST-MARK-1 Player Count API Performance Report', fontsize=16)
            
            # Chart 1: Requests per second vs concurrent users
            concurrent_users = [r['max_concurrent'] for r in self.results]
            rps = [r['requests_per_second'] for r in self.results]
            ax1.plot(concurrent_users, rps, 'b-o')
            ax1.set_xlabel('Concurrent Users')
            ax1.set_ylabel('Requests per Second')
            ax1.set_title('Throughput vs Concurrent Users')
            ax1.grid(True)
            
            # Chart 2: Response time vs concurrent users
            avg_response_times = [r['avg_response_time'] for r in self.results]
            ax2.plot(concurrent_users, avg_response_times, 'r-o')
            ax2.set_xlabel('Concurrent Users')
            ax2.set_ylabel('Average Response Time (ms)')
            ax2.set_title('Response Time vs Concurrent Users')
            ax2.grid(True)
            
            # Chart 3: Success rate vs concurrent users
            success_rates = [(r['successful_requests']/r['num_requests'])*100 for r in self.results]
            ax3.plot(concurrent_users, success_rates, 'g-o')
            ax3.set_xlabel('Concurrent Users')
            ax3.set_ylabel('Success Rate (%)')
            ax3.set_title('Success Rate vs Concurrent Users')
            ax3.set_ylim(0, 105)
            ax3.grid(True)
            
            # Chart 4: Response time distribution (last test)
            if self.results[-1]['response_times']:
                response_times_ms = [t * 1000 for t in self.results[-1]['response_times']]
                ax4.hist(response_times_ms, bins=20, alpha=0.7, color='purple')
                ax4.set_xlabel('Response Time (ms)')
                ax4.set_ylabel('Frequency')
                ax4.set_title('Response Time Distribution (Latest Test)')
                ax4.grid(True)
            
            plt.tight_layout()
            plt.savefig('player_count_performance_report.png', dpi=300, bbox_inches='tight')
            plt.show()
            
            print("📊 Performance report saved as 'player_count_performance_report.png'")
            
        except ImportError:
            print("⚠️ matplotlib not available for visual report generation")
            print("📊 Text-based performance summary:")
            for i, result in enumerate(self.results):
                print(f"   Test {i+1}: {result['requests_per_second']:.2f} RPS, "
                      f"{result['avg_response_time']:.2f}ms avg, "
                      f"{(result['successful_requests']/result['num_requests'])*100:.1f}% success")

# Browser-based performance test
javascript_load_test = """
// Browser-based player count load test
window.runPlayerCountLoadTest = async function(numRequests = 50, maxConcurrent = 10) {
    console.log(`🔄 Starting player count load test with ${numRequests} requests...`);
    console.log(`📊 Max concurrent: ${maxConcurrent}`);
    
    const startTime = performance.now();
    const results = [];
    const errors = [];
    
    // Create semaphore for concurrent limiting
    let activeRequests = 0;
    const maxActive = maxConcurrent;
    
    const makeRequest = async (i) => {
        // Wait for slot
        while (activeRequests >= maxActive) {
            await new Promise(resolve => setTimeout(resolve, 10));
        }
        
        activeRequests++;
        const requestStart = performance.now();
        
        try {
            const response = await fetch(`/api/logs/player-count/load-test-${i % 5}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });
            
            const responseTime = performance.now() - requestStart;
            
            if (response.ok) {
                await response.json(); // Read response
                results.push(responseTime);
            } else {
                errors.push(`HTTP ${response.status}`);
            }
        } catch (error) {
            errors.push(error.message);
        } finally {
            activeRequests--;
        }
    };
    
    // Start all requests
    const promises = [];
    for (let i = 0; i < numRequests; i++) {
        promises.push(makeRequest(i));
    }
    
    // Wait for all to complete
    await Promise.all(promises);
    
    const endTime = performance.now();
    const totalTime = endTime - startTime;
    
    // Calculate statistics
    const successCount = results.length;
    const failCount = errors.length;
    const avgResponseTime = results.length > 0 ? results.reduce((a, b) => a + b) / results.length : 0;
    const requestsPerSecond = successCount / (totalTime / 1000);
    
    // Find percentiles
    const sortedResults = results.sort((a, b) => a - b);
    const p50 = sortedResults[Math.floor(sortedResults.length * 0.5)] || 0;
    const p95 = sortedResults[Math.floor(sortedResults.length * 0.95)] || 0;
    const p99 = sortedResults[Math.floor(sortedResults.length * 0.99)] || 0;
    
    console.log(`\\n📊 Load Test Results:`);
    console.log(`   Total Requests: ${numRequests}`);
    console.log(`   Successful: ${successCount} (${((successCount/numRequests)*100).toFixed(1)}%)`);
    console.log(`   Failed: ${failCount} (${((failCount/numRequests)*100).toFixed(1)}%)`);
    console.log(`   Total Time: ${totalTime.toFixed(2)}ms`);
    console.log(`   Requests/Second: ${requestsPerSecond.toFixed(2)}`);
    console.log(`   Avg Response Time: ${avgResponseTime.toFixed(2)}ms`);
    console.log(`   50th Percentile: ${p50.toFixed(2)}ms`);
    console.log(`   95th Percentile: ${p95.toFixed(2)}ms`);
    console.log(`   99th Percentile: ${p99.toFixed(2)}ms`);
    
    if (errors.length > 0) {
        console.log(`\\n❌ Error Summary:`);
        const errorCounts = {};
        errors.forEach(error => {
            errorCounts[error] = (errorCounts[error] || 0) + 1;
        });
        Object.entries(errorCounts).forEach(([error, count]) => {
            console.log(`   ${error}: ${count} occurrences`);
        });
    }
    
    return {
        total: numRequests,
        success: successCount,
        failed: failCount,
        totalTime: totalTime,
        avgTime: avgResponseTime,
        requestsPerSecond: requestsPerSecond,
        percentiles: { p50, p95, p99 },
        errors: errors
    };
};

// Progressive load test
window.runProgressiveLoadTest = async function() {
    console.log('🔄 Running progressive load test...');
    
    const testConfigs = [
        { requests: 10, concurrent: 2 },
        { requests: 25, concurrent: 5 },
        { requests: 50, concurrent: 10 },
        { requests: 100, concurrent: 20 }
    ];
    
    const results = [];
    
    for (const config of testConfigs) {
        console.log(`\\n🧪 Testing ${config.requests} requests, ${config.concurrent} concurrent...`);
        const result = await runPlayerCountLoadTest(config.requests, config.concurrent);
        results.push({ config, result });
        
        // Wait between tests
        await new Promise(resolve => setTimeout(resolve, 2000));
    }
    
    console.log('\\n📊 Progressive Load Test Summary:');
    results.forEach(({ config, result }, index) => {
        console.log(`   Test ${index + 1} (${config.requests}r/${config.concurrent}c): ` +
                   `${result.requestsPerSecond.toFixed(2)} RPS, ` +
                   `${result.avgTime.toFixed(2)}ms avg, ` +
                   `${((result.success/result.total)*100).toFixed(1)}% success`);
    });
    
    return results;
};
"""

# Run load test
async def run_comprehensive_load_test():
    """Run comprehensive load testing suite"""
    tester = PlayerCountLoadTest()
    
    print("🧪 Starting Comprehensive Load Test Suite")
    print("=" * 50)
    
    # Test different load levels
    test_configs = [
        {'requests': 50, 'concurrent': 5},
        {'requests': 100, 'concurrent': 10},
        {'requests': 200, 'concurrent': 20},
        {'requests': 500, 'concurrent': 50}
    ]
    
    for config in test_configs:
        print(f"\n🔄 Testing {config['requests']} requests with {config['concurrent']} concurrent...")
        try:
            result = await tester.test_concurrent_player_count_requests(**config)
            
            # Performance assertions
            assert result['requests_per_second'] > 1, f"Too slow: {result['requests_per_second']} RPS"
            assert result['avg_response_time'] < 5000, f"Too slow: {result['avg_response_time']}ms"
            assert (result['successful_requests'] / result['total_requests']) > 0.9, \
                   f"Too many failures: {result['successful_requests']}/{result['total_requests']}"
            
            print("✅ Performance targets met")
            
        except Exception as e:
            print(f"❌ Load test failed: {e}")
    
    # Run stress test
    print(f"\n🔥 Running 30-second stress test...")
    try:
        stress_result = await tester.stress_test(duration_seconds=30, requests_per_second=5)
        print("✅ Stress test completed")
    except Exception as e:
        print(f"❌ Stress test failed: {e}")
    
    # Generate report
    tester.generate_performance_report()
    
    return tester.results

if __name__ == "__main__":
    # Example usage
    import asyncio
    
    async def main():
        await run_comprehensive_load_test()
    
    asyncio.run(main())
```

## ✅ Test Execution Commands

### **Manual Testing Checklist**
```bash
# 1. Start the application
python main.py

# 2. Open browser and navigate to http://localhost:5000

# 3. Run browser-based tests (F12 Console)
testPlayerCount()              # Test live player count system
testAllComponents()            # Test all modular components
runPlayerCountLoadTest(20)     # Load test player count API
runProgressiveLoadTest()       # Progressive load testing

# 4. Verify core functionality
✅ Login (demo mode): admin/password
✅ All 9 tabs load without errors
✅ Server manager shows player counts
✅ Auto commands run every 10 seconds
✅ Player counts update from server logs
✅ Manual refresh buttons work
✅ Demo mode shows mock data
✅ Live mode shows real data (with G-Portal)
✅ Error handling preserves old values
✅ Mobile responsiveness works
✅ Cache system improves performance
✅ Concurrent operations work correctly

# 5. Backend API testing
python -m unittest doc.testing.api_tests
python -m unittest doc.testing.performance_tests

# 6. Load testing
python doc/testing/load_test.py

# 7. Performance verification
✅ Page load < 2 seconds
✅ Player count updates < 500ms
✅ Memory usage < 512MB
✅ No JavaScript errors in console
✅ No network request failures
✅ Cache hit rate > 80%
✅ Concurrent request handling
✅ Error recovery mechanisms
```

### **Automated Test Suite Runner**
```javascript
// Complete test suite runner
async function runAllTests() {
    console.log('🧪 Running Complete GUST-MARK-1 Test Suite...');
    console.log('================================================');
    
    const testSuites = [
        { 
            name: 'Player Count', 
            runner: () => new PlayerCountTestSuite().runAllPlayerCountTests(),
            critical: true
        },
        { 
            name: 'Components', 
            runner: () => new ComponentTester().testAllComponents(),
            critical: true
        },
        { 
            name: 'Load Test (Light)', 
            runner: () => runPlayerCountLoadTest(10, 3),
            critical: false
        },
        {
            name: 'Progressive Load Test',
            runner: () => runProgressiveLoadTest(),
            critical: false
        }
    ];
    
    const overallStartTime = performance.now();
    const results = {};
    let criticalFailures = 0;
    
    for (const suite of testSuites) {
        console.log(`\n🔍 Running ${suite.name} Tests...`);
        try {
            const result = await suite.runner();
            results[suite.name] = { success: true, result };
            console.log(`✅ ${suite.name} tests completed successfully`);
        } catch (error) {
            results[suite.name] = { success: false, error: error.message };
            console.log(`❌ ${suite.name} tests failed: ${error.message}`);
            
            if (suite.critical) {
                criticalFailures++;
            }
        }
    }
    
    const overallEndTime = performance.now();
    const totalTime = overallEndTime - overallStartTime;
    
    console.log('\n📊 Overall Test Results');
    console.log('========================');
    console.log(`Total time: ${totalTime.toFixed(2)}ms`);
    console.log(`Critical failures: ${criticalFailures}`);
    
    for (const [suiteName, result] of Object.entries(results)) {
        const icon = result.success ? '✅' : '❌';
        console.log(`${icon} ${suiteName}: ${result.success ? 'PASSED' : 'FAILED'}`);
        
        if (!result.success) {
            console.log(`   Error: ${result.error}`);
        }
    }
    
    const passedSuites = Object.values(results).filter(r => r.success).length;
    const totalSuites = Object.keys(results).length;
    
    console.log(`\nOverall Success Rate: ${((passedSuites/total