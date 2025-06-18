"""
Missing Routes Fix for GUST Bot
==============================
Add missing endpoints: /health, /api/console/output, /api/clans
"""

# Add these routes to your app.py in the setup_routes() method
# Insert after the existing route registrations

def add_missing_routes_to_app_py():
    """
    Add this code to your app.py setup_routes() method
    Insert after the existing blueprint registrations
    """
    
    # Add these imports at the top of app.py if not already present
    """
    from datetime import datetime
    """
    
    # Add these routes in setup_routes() method after blueprint registrations
    """
    print("🔍 DEBUG: Adding missing routes")
    
    # Health check endpoint
    @self.app.route('/health')
    def health_check():
        '''Health check endpoint'''
        try:
            health_data = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'version': '1.0.0',
                'uptime': 'active',
                'database': 'MongoDB' if self.db else 'InMemoryStorage',
                'websockets_available': WEBSOCKETS_AVAILABLE,
                'live_connections': len(getattr(self, 'websocket_manager', {}).connections) if hasattr(self, 'websocket_manager') and self.websocket_manager else 0,
                'managed_servers': len(managedServers) if 'managedServers' in globals() else len(self.servers),
                'user_storage_type': type(self.user_storage).__name__ if self.user_storage else 'None',
                'features': {
                    'user_management': bool(self.user_storage and hasattr(self.user_storage, 'register')),
                    'console_commands': True,
                    'live_console': WEBSOCKETS_AVAILABLE,
                    'event_management': hasattr(self, 'vanilla_koth'),
                    'clan_management': True,
                    'economy_system': True,
                    'gambling_system': True
                }
            }
            return jsonify(health_data)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }), 500
    
    # Console output endpoint
    @self.app.route('/api/console/output')
    @require_auth
    def get_console_output():
        '''Get console output'''
        try:
            output = []
            if hasattr(self, 'console_output') and self.console_output:
                output = list(self.console_output)
            else:
                # Return basic console status
                output = [
                    {
                        'timestamp': datetime.now().isoformat(),
                        'message': 'GUST Bot Console - Ready',
                        'status': 'system',
                        'source': 'console_system'
                    }
                ]
            return jsonify(output)
        except Exception as e:
            return jsonify([{
                'timestamp': datetime.now().isoformat(),
                'message': f'Console output error: {str(e)}',
                'status': 'error',
                'source': 'console_system'
            }]), 500
    
    # Clans endpoint  
    @self.app.route('/api/clans')
    @require_auth
    def get_clans():
        '''Get list of clans'''
        try:
            clans = []
            if self.db:
                clans = list(self.db.clans.find({}, {'_id': 0}))
            else:
                clans = getattr(self, 'clans', [])
            return jsonify(clans)
        except Exception as e:
            return jsonify({'error': f'Failed to retrieve clans: {str(e)}'}), 500
    
    print("✅ Added missing routes: health, console/output, clans")
    """

# COMPLETE CODE TO ADD TO YOUR app.py setup_routes() method:

COMPLETE_ROUTES_CODE = '''
        print("🔍 DEBUG: Adding missing routes")
        
        # Health check endpoint
        @self.app.route('/health')
        def health_check():
            """Health check endpoint"""
            try:
                health_data = {
                    'status': 'healthy',
                    'timestamp': datetime.now().isoformat(),
                    'version': '1.0.0',
                    'uptime': 'active',
                    'database': 'MongoDB' if self.db else 'InMemoryStorage',
                    'websockets_available': WEBSOCKETS_AVAILABLE,
                    'live_connections': len(getattr(self.websocket_manager, 'connections', {})) if hasattr(self, 'websocket_manager') and self.websocket_manager else 0,
                    'managed_servers': len(self.servers),
                    'user_storage_type': type(self.user_storage).__name__ if self.user_storage else 'None',
                    'features': {
                        'user_management': bool(self.user_storage and hasattr(self.user_storage, 'register')),
                        'console_commands': True,
                        'live_console': WEBSOCKETS_AVAILABLE,
                        'event_management': hasattr(self, 'vanilla_koth'),
                        'clan_management': True,
                        'economy_system': True,
                        'gambling_system': True
                    }
                }
                return jsonify(health_data)
            except Exception as e:
                return jsonify({
                    'status': 'error',
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e)
                }), 500
        
        # Console output endpoint
        @self.app.route('/api/console/output')
        @require_auth
        def get_console_output():
            """Get console output"""
            try:
                output = []
                if hasattr(self, 'console_output') and self.console_output:
                    output = list(self.console_output)
                else:
                    # Return basic console status
                    output = [
                        {
                            'timestamp': datetime.now().isoformat(),
                            'message': 'GUST Bot Console - Ready',
                            'status': 'system',
                            'source': 'console_system'
                        }
                    ]
                return jsonify(output)
            except Exception as e:
                return jsonify([{
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Console output error: {str(e)}',
                    'status': 'error',
                    'source': 'console_system'
                }]), 500
        
        # Clans endpoint  
        @self.app.route('/api/clans')
        @require_auth
        def get_clans():
            """Get list of clans"""
            try:
                clans = []
                if self.db:
                    clans = list(self.db.clans.find({}, {'_id': 0}))
                else:
                    clans = getattr(self, 'clans', [])
                return jsonify(clans)
            except Exception as e:
                return jsonify({'error': f'Failed to retrieve clans: {str(e)}'}), 500
        
        print("✅ Added missing routes: health, console/output, clans")
'''

print("Copy the COMPLETE_ROUTES_CODE above and add it to your app.py setup_routes() method")
print("Add it right before the final debug print statement")
