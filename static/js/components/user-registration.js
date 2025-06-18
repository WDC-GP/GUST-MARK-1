/**
 * User Registration Component
 * ===========================
 * Handle user registration and profile management
 */

class UserRegistration {
    constructor(containerId, options = {}) {
        this.container = document.getElementById(containerId);
        this.options = {
            showProfile: true,
            autoRegister: false,
            onUserRegistered: null,
            ...options
        };
        this.currentUser = null;
        this.api = window.gustAPI;

        this.init();
    }

    async init() {
        this.render();
        this.attachEventListeners();

        // Check for existing user
        const savedUser = localStorage.getItem('gust_current_user');
        if (savedUser) {
            await this.loadUserProfile(savedUser);
        }
    }

    render() {
        this.container.innerHTML = 
            <div class="user-registration">
                <!-- User Status Bar -->
                <div id="userStatusBar" class="bg-gray-800 p-4 rounded-lg mb-4 border border-gray-700">
                    <div class="flex items-center justify-between">
                        <div id="userInfo" class="flex items-center space-x-3">
                            <div class="w-10 h-10 bg-purple-600 rounded-full flex items-center justify-center">
                                <span class="text-white font-bold" id="userAvatar">?</span>
                            </div>
                            <div>
                                <div class="font-semibold" id="userDisplayName">Not logged in</div>
                                <div class="text-sm text-gray-400" id="userSubtext">Click to register or login</div>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <button id="profileBtn" class="bg-purple-600 hover:bg-purple-700 text-white px-3 py-1 rounded text-sm">
                                Profile
                            </button>
                            <button id="logoutBtn" class="bg-gray-600 hover:bg-gray-700 text-white px-3 py-1 rounded text-sm hidden">
                                Logout
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Registration Modal -->
                <div id="registrationModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
                    <div class="bg-gray-800 p-6 rounded-lg max-w-md w-full mx-4">
                        <h3 class="text-xl font-bold mb-4">🎮 User Registration</h3>
                        <div class="space-y-4">
                            <div>
                                <label class="block text-sm font-medium mb-2">G-Portal Username *</label>
                                <input type="text" id="userIdInput" placeholder="Your G-Portal login"
                                       class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500 focus:outline-none">
                                <div class="text-xs text-gray-400 mt-1">This will be your unique identifier</div>
                            </div>
                            <div>
                                <label class="block text-sm font-medium mb-2">Display Nickname *</label>
                                <input type="text" id="nicknameInput" placeholder="How others see you"
                                       class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500 focus:outline-none">
                                <div class="text-xs text-gray-400 mt-1">You can change this later</div>
                            </div>
                        </div>
                        <div class="flex space-x-3 mt-6">
                            <button id="registerBtn" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded flex-1">
                                Register
                            </button>
                            <button id="cancelRegisterBtn" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded flex-1">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>

                <!-- Profile Modal -->
                <div id="profileModal" class="hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center">
                    <div class="bg-gray-800 p-6 rounded-lg max-w-lg w-full mx-4">
                        <h3 class="text-xl font-bold mb-4">👤 User Profile</h3>
                        <div id="profileContent" class="space-y-4">
                            <!-- Profile content will be populated dynamically -->
                        </div>
                        <div class="flex space-x-3 mt-6">
                            <button id="saveProfileBtn" class="bg-purple-600 hover:bg-purple-700 text-white px-4 py-2 rounded flex-1">
                                Save Changes
                            </button>
                            <button id="closeProfileBtn" class="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded flex-1">
                                Close
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        ;
    }

    renderProfileContent() {
        if (!this.currentUser) return;

        const content = this.container.querySelector('#profileContent');
        content.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                    <label class="block text-sm font-medium mb-2">User ID</label>
                    <input type="text" value="${this.currentUser.userId}" disabled
                           class="w-full bg-gray-600 p-3 rounded border border-gray-600 text-gray-400">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Display Nickname</label>
                    <input type="text" id="profileNickname" value="${this.currentUser.nickname}"
                           class="w-full bg-gray-700 p-3 rounded border border-gray-600 focus:border-purple-500 focus:outline-none">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Registered</label>
                    <input type="text" value="${new Date(this.currentUser.registeredAt).toLocaleDateString()}" disabled
                           class="w-full bg-gray-600 p-3 rounded border border-gray-600 text-gray-400">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Total Servers</label>
                    <input type="text" value="${this.currentUser.totalServers || 0}" disabled
                           class="w-full bg-gray-600 p-3 rounded border border-gray-600 text-gray-400">
                </div>
            </div>

            <div class="mt-4">
                <h4 class="font-semibold mb-2">Preferences</h4>
                <div class="space-y-2">
                    <label class="flex items-center">
                        <input type="checkbox" id="displayNickname" ${this.currentUser.preferences?.displayNickname ? 'checked' : ''}
                               class="mr-2">
                        Display nickname in leaderboards
                    </label>
                    <label class="flex items-center">
                        <input type="checkbox" id="showInLeaderboards" ${this.currentUser.preferences?.showInLeaderboards ? 'checked' : ''}
                               class="mr-2">
                        Show in public leaderboards
                    </label>
                </div>
            </div>

            ${Object.keys(this.currentUser.servers || `).length > 0 ? `
                <div class="mt-4">
                    <h4 class="font-semibold mb-2">Server Memberships</h4>
                    <div class="space-y-2 max-h-32 overflow-y-auto">
                        ${Object.entries(this.currentUser.servers).map(([serverId, serverData]) => `
                            <div class="bg-gray-700 p-2 rounded text-sm">
                                <div class="font-medium">${serverId}</div>
                                <div class="text-gray-400">Balance: ${serverData.balance || 0} coins${serverData.clanTag ? ` | Clan: ${serverData.clanTag}` : ''}</div>
                            </div>
                        `).join('')}
                    </div>
                </div>
            ` : ''}
        `;
    }

    // Rest of the methods remain the same...
    attachEventListeners() {
        // User status bar click
        this.container.querySelector('#userInfo')?.addEventListener('click', () => {
            if (!this.currentUser) {
                this.showRegistrationModal();
            }
        });

        // Profile button
        this.container.querySelector('#profileBtn')?.addEventListener('click', () => {
            if (this.currentUser) {
                this.showProfileModal();
            } else {
                this.showRegistrationModal();
            }
        });

        // Logout button
        this.container.querySelector('#logoutBtn')?.addEventListener('click', () => {
            this.logout();
        });

        // Registration modal
        this.container.querySelector('#registerBtn')?.addEventListener('click', () => {
            this.register();
        });

        this.container.querySelector('#cancelRegisterBtn')?.addEventListener('click', () => {
            this.hideRegistrationModal();
        });

        // Profile modal
        this.container.querySelector('#saveProfileBtn')?.addEventListener('click', () => {
            this.saveProfile();
        });

        this.container.querySelector('#closeProfileBtn')?.addEventListener('click', () => {
            this.hideProfileModal();
        });

        // Modal backdrop clicks
        this.container.querySelector('#registrationModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'registrationModal') this.hideRegistrationModal();
        });

        this.container.querySelector('#profileModal')?.addEventListener('click', (e) => {
            if (e.target.id === 'profileModal') this.hideProfileModal();
        });
    }

    showRegistrationModal() {
        const modal = this.container.querySelector('#registrationModal');
        modal?.classList.remove('hidden');

        // Clear inputs
        this.container.querySelector('#userIdInput').value = '';
        this.container.querySelector('#nicknameInput').value = '';

        // Focus first input
        this.container.querySelector('#userIdInput')?.focus();
    }

    hideRegistrationModal() {
        const modal = this.container.querySelector('#registrationModal');
        modal?.classList.add('hidden');
    }

    showProfileModal() {
        if (!this.currentUser) return;

        this.renderProfileContent();
        const modal = this.container.querySelector('#profileModal');
        modal?.classList.remove('hidden');
    }

    hideProfileModal() {
        const modal = this.container.querySelector('#profileModal');
        modal?.classList.add('hidden');
    }

    async register() {
        const userId = this.container.querySelector('#userIdInput').value.trim();
        const nickname = this.container.querySelector('#nicknameInput').value.trim();

        if (!userId) {
            alert('Please enter your G-Portal username');
            return;
        }

        if (!nickname) {
            alert('Please enter a display nickname');
            return;
        }

        try {
            const result = await this.api.registerUser(userId, nickname);

            if (result.success) {
                this.currentUser = result.user;
                this.api.setCurrentUser(userId);
                this.updateUserDisplay();
                this.hideRegistrationModal();

                if (this.options.onUserRegistered) {
                    this.options.onUserRegistered(this.currentUser);
                }

                // Emit global event
                document.dispatchEvent(new CustomEvent('userRegistered', {
                    detail: { user: this.currentUser }
                }));

                console.log(User registered: ${nickname} (${userId}));
            } else {
                alert(result.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Registration error:', error);
            alert('Registration failed: ' + error.message);
        }
    }

    async loadUserProfile(userId) {
        try {
            const result = await this.api.getUserProfile(userId);

            if (result.success) {
                this.currentUser = result.user;
                this.api.setCurrentUser(userId);
                this.updateUserDisplay();
            } else {
                // User not found, clear saved data
                localStorage.removeItem('gust_current_user');
                this.currentUser = null;
                this.updateUserDisplay();
            }
        } catch (error) {
            console.error('Error loading user profile:', error);
            this.currentUser = null;
            this.updateUserDisplay();
        }
    }

    async saveProfile() {
        if (!this.currentUser) return;

        const nickname = this.container.querySelector('#profileNickname').value.trim();
        const displayNickname = this.container.querySelector('#displayNickname').checked;
        const showInLeaderboards = this.container.querySelector('#showInLeaderboards').checked;

        if (!nickname) {
            alert('Please enter a nickname');
            return;
        }

        try {
            const updates = {
                nickname,
                preferences: {
                    displayNickname,
                    showInLeaderboards
                }
            };

            const result = await this.api.updateUserProfile(this.currentUser.userId, updates);

            if (result.success) {
                this.currentUser = { ...this.currentUser, ...updates };
                this.updateUserDisplay();
                this.hideProfileModal();
                console.log('Profile updated successfully');
            } else {
                alert(result.error || 'Failed to update profile');
            }
        } catch (error) {
            console.error('Error updating profile:', error);
            alert('Failed to update profile: ' + error.message);
        }
    }

    logout() {
        this.currentUser = null;
        localStorage.removeItem('gust_current_user');
        this.api.setCurrentUser(null);
        this.updateUserDisplay();

        // Emit global event
        document.dispatchEvent(new CustomEvent('userLoggedOut'));

        console.log('User logged out');
    }

    updateUserDisplay() {
        const avatar = this.container.querySelector('#userAvatar');
        const displayName = this.container.querySelector('#userDisplayName');
        const subtext = this.container.querySelector('#userSubtext');
        const logoutBtn = this.container.querySelector('#logoutBtn');

        if (this.currentUser) {
            avatar.textContent = this.currentUser.nickname.charAt(0).toUpperCase();
            displayName.textContent = this.currentUser.nickname;
            subtext.textContent = ID: ${this.currentUser.userId} | ${this.currentUser.totalServers || 0} servers;
            logoutBtn.classList.remove('hidden');
        } else {
            avatar.textContent = '?';
            displayName.textContent = 'Not logged in';
            subtext.textContent = 'Click to register or login';
            logoutBtn.classList.add('hidden');
        }
    }

    getCurrentUser() {
        return this.currentUser;
    }
}

// Make available globally
window.UserRegistration = UserRegistration;

export { UserRegistration };
