/**
 * Frontend Integration Tests
 * ==========================
 * Test frontend components with server-specific functionality
 */

class FrontendTestSuite {
    constructor() {
        this.tests = [];
        this.results = {
            passed: 0,
            failed: 0,
            total: 0
        };
    }

    addTest(name, testFunction) {
        this.tests.push({ name, testFunction });
    }

    async runTests() {
        console.log('🧪 Running Frontend Integration Tests...');
        console.log('=====================================');

        for (const test of this.tests) {
            try {
                await test.testFunction();
                console.log(✅ );
                this.results.passed++;
            } catch (error) {
                console.error(❌ : );
                this.results.failed++;
            }
            this.results.total++;
        }

        console.log('\\n📊 Frontend Test Results:');
        console.log(Total: );
        console.log(Passed: );
        console.log(Failed: );
        console.log(Success Rate: %);

        return this.results.failed === 0;
    }
}

// Test suite setup
const testSuite = new FrontendTestSuite();

// API Client Tests
testSuite.addTest('API Client Initialization', async () => {
    if (!window.gustAPI) {
        throw new Error('Global API client not available');
    }
    if (typeof window.gustAPI.setCurrentServer !== 'function') {
        throw new Error('API client missing server management methods');
    }
});

testSuite.addTest('Server Context Management', async () => {
    window.gustAPI.setCurrentServer('test_server');
    const current = window.gustAPI.getCurrentServer();
    if (current !== 'test_server') {
        throw new Error('Server context not properly stored');
    }
});

testSuite.addTest('User Context Management', async () => {
    window.gustAPI.setCurrentUser('test_user');
    const current = window.gustAPI.getCurrentUser();
    if (current !== 'test_user') {
        throw new Error('User context not properly stored');
    }
});

// Component Tests
testSuite.addTest('ServerSelector Component', async () => {
    const container = document.createElement('div');
    container.id = 'test-server-selector';
    document.body.appendChild(container);
    
    const selector = new ServerSelector('test-server-selector', {
        showAddServer: false,
        allowEmpty: true
    });
    
    if (!selector.container) {
        throw new Error('ServerSelector failed to initialize');
    }
    
    document.body.removeChild(container);
});

testSuite.addTest('UserRegistration Component', async () => {
    const container = document.createElement('div');
    container.id = 'test-user-registration';
    document.body.appendChild(container);
    
    const registration = new UserRegistration('test-user-registration', {
        autoRegister: false
    });
    
    if (!registration.container) {
        throw new Error('UserRegistration failed to initialize');
    }
    
    document.body.removeChild(container);
});

testSuite.addTest('EnhancedDashboard Component', async () => {
    const container = document.createElement('div');
    container.id = 'test-dashboard';
    document.body.appendChild(container);
    
    const dashboard = new EnhancedDashboard('test-dashboard', {
        autoRefresh: false
    });
    
    if (!dashboard.container) {
        throw new Error('EnhancedDashboard failed to initialize');
    }
    
    dashboard.destroy();
    document.body.removeChild(container);
});

// API Integration Tests
testSuite.addTest('Server-Specific API Calls', async () => {
    // Mock server context
    window.gustAPI.setCurrentServer('test_server');
    window.gustAPI.setCurrentUser('test_user');
    
    // Test that API methods use server context
    const balanceEndpoint = '/api/economy/balance/test_user/test_server';
    const mockBalance = window.gustAPI.getBalance('test_user');
    
    // This would normally make a real API call
    // For testing, we just verify the method exists and accepts parameters
    if (typeof mockBalance?.then !== 'function') {
        throw new Error('API methods should return promises');
    }
});

testSuite.addTest('Currency Formatting', async () => {
    const formatted = window.gustAPI.formatCurrency(1234567);
    if (formatted !== '1,234,567') {
        throw new Error(Expected '1,234,567', got '');
    }
});

testSuite.addTest('Validation Methods', async () => {
    if (!window.gustAPI.validateServerId('server_123')) {
        throw new Error('Valid server ID should pass validation');
    }
    if (window.gustAPI.validateServerId('')) {
        throw new Error('Empty server ID should fail validation');
    }
    if (!window.gustAPI.validateUserId('user_123')) {
        throw new Error('Valid user ID should pass validation');
    }
    if (window.gustAPI.validateUserId('')) {
        throw new Error('Empty user ID should fail validation');
    }
});

// Event System Tests
testSuite.addTest('Server Change Events', async () => {
    return new Promise((resolve, reject) => {
        const timeout = setTimeout(() => {
            reject(new Error('Server change event not fired'));
        }, 1000);

        document.addEventListener('serverChanged', (e) => {
            clearTimeout(timeout);
            if (e.detail.serverId === 'event_test_server') {
                resolve();
            } else {
                reject(new Error('Incorrect server ID in event'));
            }
        }, { once: true });

        // Trigger server change
        const container = document.createElement('div');
        container.id = 'test-event-selector';
        document.body.appendChild(container);
        
        const selector = new ServerSelector('test-event-selector');
        selector.selectServer('event_test_server');
        
        document.body.removeChild(container);
    });
});

// Run tests when page loads
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        setTimeout(() => testSuite.runTests(), 1000);
    });
} else {
    setTimeout(() => testSuite.runTests(), 1000);
}

// Make available globally for manual testing
window.FrontendTestSuite = FrontendTestSuite;
window.runFrontendTests = () => testSuite.runTests();
