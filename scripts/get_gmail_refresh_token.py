#!/usr/bin/env python3
"""
Gmail OAuth 2.0 Refresh Token Setup Script

This script helps you obtain the refresh token needed for Gmail OAuth 2.0 email sending.
Run this ONCE to get the refresh token, then add it to your .env file.

Usage:
1. Set GMAIL_CLIENT_ID and GMAIL_CLIENT_SECRET in .env or as environment variables
2. Run this script: python scripts/get_gmail_refresh_token.py
3. A browser window will open for Google authorization
4. Sign in with the Gmail account you want to send from
5. Grant the requested permissions
6. Copy the refresh token from the output
7. Add it to your .env file: GMAIL_REFRESH_TOKEN=your_token_here

Requirements:
- pip install google-auth google-auth-oauthlib google-api-python-client

Author: Super Manager AI
"""

import os
import sys
import json
import webbrowser
import http.server
import socketserver
import urllib.parse
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent.parent / 'backend' / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False

# Configuration from environment
CLIENT_ID = os.getenv("GMAIL_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("GMAIL_CLIENT_SECRET", "")
REDIRECT_PORT = 3333
REDIRECT_URI = f"http://localhost:{REDIRECT_PORT}"
SCOPES = ['https://www.googleapis.com/auth/gmail.send']

# ANSI colors for pretty output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def print_banner():
    """Print a nice banner"""
    print(f"""
{Colors.CYAN}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   {Colors.BOLD}🔐 Gmail OAuth 2.0 Refresh Token Setup{Colors.CYAN}                        ║
║                                                                  ║
║   This script will help you get a refresh token for Gmail       ║
║   OAuth authentication in Super Manager AI                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")


def check_dependencies():
    """Check if required dependencies are installed"""
    if not GOOGLE_LIBS_AVAILABLE:
        print(f"""
{Colors.FAIL}❌ Required libraries not installed!{Colors.ENDC}

Please install the required packages:

{Colors.CYAN}pip install google-auth google-auth-oauthlib google-api-python-client python-dotenv{Colors.ENDC}

Or install all requirements:

{Colors.CYAN}pip install -r requirements.txt{Colors.ENDC}
""")
        sys.exit(1)
    
    # Check for credentials
    if not CLIENT_ID or not CLIENT_SECRET:
        print(f"""
{Colors.FAIL}❌ Gmail OAuth credentials not found!{Colors.ENDC}

Please set the following environment variables in your .env file:

{Colors.CYAN}GMAIL_CLIENT_ID=your_client_id_here
GMAIL_CLIENT_SECRET=your_client_secret_here{Colors.ENDC}

You can get these from Google Cloud Console:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Gmail API
4. Create OAuth 2.0 credentials
5. Copy Client ID and Client Secret to your .env file
""")
        sys.exit(1)
    
    print(f"{Colors.GREEN}✅ All dependencies installed{Colors.ENDC}")
    print(f"{Colors.GREEN}✅ OAuth credentials found{Colors.ENDC}")


def create_oauth_config():
    """Create the OAuth client configuration"""
    return {
        "installed": {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "redirect_uris": [REDIRECT_URI, "urn:ietf:wg:oauth:2.0:oob"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs"
        }
    }


class OAuthCallbackHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for OAuth callback"""
    
    def __init__(self, *args, flow=None, **kwargs):
        self.flow = flow
        super().__init__(*args, **kwargs)
    
    def log_message(self, format, *args):
        # Suppress HTTP server logs
        pass
    
    def do_GET(self):
        """Handle the OAuth callback"""
        # Parse the authorization response
        parsed_url = urllib.parse.urlparse(self.path)
        query_params = urllib.parse.parse_qs(parsed_url.query)
        
        if 'code' in query_params:
            auth_code = query_params['code'][0]
            
            # Return success page
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Authorization Successful</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
        }
        h1 {
            color: #10b981;
            margin-bottom: 20px;
        }
        p {
            color: #64748b;
            line-height: 1.6;
        }
        .emoji {
            font-size: 60px;
            margin-bottom: 20px;
        }
        .note {
            background: #f0fdf4;
            border: 1px solid #86efac;
            padding: 15px;
            border-radius: 10px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="emoji">✅</div>
        <h1>Authorization Successful!</h1>
        <p>You have successfully authorized Super Manager AI to send emails on your behalf.</p>
        <div class="note">
            <strong>👉 Next Step:</strong><br>
            Check your terminal window for the refresh token and add it to your .env file.
        </div>
        <p style="margin-top: 20px; color: #94a3b8; font-size: 14px;">
            You can close this window now.
        </p>
    </div>
</body>
</html>
"""
            self.wfile.write(success_html.encode())
            
            # Store the auth code
            self.server.auth_code = auth_code
            
        elif 'error' in query_params:
            error = query_params.get('error', ['Unknown error'])[0]
            error_description = query_params.get('error_description', [''])[0]
            
            self.send_response(400)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            error_html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Authorization Failed</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background: linear-gradient(135deg, #ef4444 0%, #b91c1c 100%);
        }}
        .container {{
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            text-align: center;
            max-width: 500px;
        }}
        h1 {{ color: #ef4444; }}
        .error {{ background: #fef2f2; border: 1px solid #fca5a5; padding: 15px; border-radius: 10px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>❌ Authorization Failed</h1>
        <div class="error">
            <strong>Error:</strong> {error}<br>
            {error_description}
        </div>
        <p>Please try again or check your OAuth configuration.</p>
    </div>
</body>
</html>
"""
            self.wfile.write(error_html.encode())
            self.server.auth_code = None
        else:
            self.send_response(404)
            self.end_headers()


def get_refresh_token():
    """Run the OAuth flow and get the refresh token"""
    
    gmail_user = os.getenv("GMAIL_USER", "your Gmail account")
    print(f"\n{Colors.BLUE}📧 Email to authorize: {gmail_user}{Colors.ENDC}")
    print(f"\n{Colors.WARNING}⚠️  Important: Sign in with the Gmail account you want to send emails from!{Colors.ENDC}\n")
    
    # Create the OAuth config
    client_config = create_oauth_config()
    
    # Create the flow
    flow = InstalledAppFlow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    
    # Generate authorization URL
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'  # Force consent to get refresh token
    )
    
    print(f"{Colors.CYAN}🌐 Opening browser for authorization...{Colors.ENDC}")
    print(f"\n{Colors.BOLD}If the browser doesn't open, visit this URL manually:{Colors.ENDC}")
    print(f"{Colors.BLUE}{auth_url}{Colors.ENDC}\n")
    
    # Open browser
    webbrowser.open(auth_url)
    
    # Start local server to catch callback
    print(f"{Colors.CYAN}🔄 Waiting for authorization (listening on port {REDIRECT_PORT})...{Colors.ENDC}\n")
    
    class OAuthServer(socketserver.TCPServer):
        allow_reuse_address = True
        auth_code = None
    
    handler = lambda *args, **kwargs: OAuthCallbackHandler(*args, flow=flow, **kwargs)
    
    try:
        with OAuthServer(("", REDIRECT_PORT), handler) as httpd:
            # Handle one request (the callback)
            httpd.handle_request()
            auth_code = httpd.auth_code
    except OSError as e:
        print(f"{Colors.FAIL}❌ Failed to start server on port {REDIRECT_PORT}: {e}{Colors.ENDC}")
        print(f"Try closing any other servers or change REDIRECT_PORT in the script.")
        sys.exit(1)
    
    if not auth_code:
        print(f"{Colors.FAIL}❌ Authorization failed or was cancelled.{Colors.ENDC}")
        sys.exit(1)
    
    # Exchange auth code for tokens
    print(f"{Colors.CYAN}🔄 Exchanging authorization code for tokens...{Colors.ENDC}")
    
    try:
        flow.fetch_token(code=auth_code)
        credentials = flow.credentials
        
        print(f"""
{Colors.GREEN}╔══════════════════════════════════════════════════════════════════╗
║                                                                  ║
║   {Colors.BOLD}✅ SUCCESS! Here is your refresh token:{Colors.GREEN}                       ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝{Colors.ENDC}
""")
        
        print(f"{Colors.BOLD}Refresh Token:{Colors.ENDC}")
        print(f"{Colors.CYAN}{credentials.refresh_token}{Colors.ENDC}")
        
        gmail_user = os.getenv("GMAIL_USER", "your_email@gmail.com")
        print(f"""
{Colors.GREEN}═══════════════════════════════════════════════════════════════════{Colors.ENDC}

{Colors.BOLD}📝 Add this to your .env file:{Colors.ENDC}

{Colors.CYAN}GMAIL_REFRESH_TOKEN={credentials.refresh_token}{Colors.ENDC}

{Colors.BOLD}📋 Full Gmail OAuth configuration for .env:{Colors.ENDC}

{Colors.CYAN}# Gmail OAuth Configuration
GMAIL_CLIENT_ID={CLIENT_ID}
GMAIL_CLIENT_SECRET={CLIENT_SECRET}
GMAIL_REFRESH_TOKEN={credentials.refresh_token}
GMAIL_USER={gmail_user}{Colors.ENDC}

{Colors.GREEN}═══════════════════════════════════════════════════════════════════{Colors.ENDC}

{Colors.BOLD}📊 Token Details:{Colors.ENDC}
- Access Token: {Colors.GREEN}✅ Received{Colors.ENDC}
- Refresh Token: {Colors.GREEN}✅ Received{Colors.ENDC}
- Token Expiry: {credentials.expiry if credentials.expiry else 'N/A'}
- Scopes: {', '.join(credentials.scopes) if credentials.scopes else SCOPES}

{Colors.WARNING}⚠️  Keep your refresh token secret! Don't commit it to version control.{Colors.ENDC}
""")
        
        # Optionally save to .env file
        env_file = Path(__file__).parent.parent / 'backend' / '.env'
        if env_file.exists():
            print(f"{Colors.CYAN}Would you like to automatically add the token to {env_file}? (y/n): {Colors.ENDC}", end='')
            response = input().strip().lower()
            
            if response == 'y':
                with open(env_file, 'a') as f:
                    f.write(f"\n# Gmail OAuth (added by setup script)\n")
                    f.write(f"GMAIL_REFRESH_TOKEN={credentials.refresh_token}\n")
                print(f"{Colors.GREEN}✅ Token added to .env file!{Colors.ENDC}")
            else:
                print(f"{Colors.BLUE}👍 No problem! Add it manually when ready.{Colors.ENDC}")
        
        return credentials.refresh_token
        
    except Exception as e:
        print(f"{Colors.FAIL}❌ Failed to exchange code for tokens: {e}{Colors.ENDC}")
        sys.exit(1)


def test_token(refresh_token: str):
    """Test that the refresh token works"""
    print(f"\n{Colors.CYAN}🧪 Testing the refresh token...{Colors.ENDC}")
    
    try:
        credentials = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            scopes=SCOPES
        )
        
        # Try to refresh
        credentials.refresh(Request())
        
        if credentials.valid:
            print(f"{Colors.GREEN}✅ Token is valid and working!{Colors.ENDC}")
            print(f"   Access token obtained, expires: {credentials.expiry}")
            return True
        else:
            print(f"{Colors.WARNING}⚠️  Token refreshed but validity check failed{Colors.ENDC}")
            return False
            
    except Exception as e:
        print(f"{Colors.FAIL}❌ Token test failed: {e}{Colors.ENDC}")
        return False


def main():
    """Main entry point"""
    print_banner()
    check_dependencies()
    
    print(f"""
{Colors.BOLD}What would you like to do?{Colors.ENDC}

1. Get a new refresh token (authorize Gmail)
2. Test an existing refresh token
3. Exit

""")
    
    choice = input(f"{Colors.CYAN}Enter your choice (1-3): {Colors.ENDC}").strip()
    
    if choice == '1':
        refresh_token = get_refresh_token()
        if refresh_token:
            test_token(refresh_token)
    
    elif choice == '2':
        token = input(f"{Colors.CYAN}Enter your refresh token: {Colors.ENDC}").strip()
        if token:
            test_token(token)
        else:
            print(f"{Colors.WARNING}No token provided.{Colors.ENDC}")
    
    elif choice == '3':
        print(f"{Colors.BLUE}Goodbye! 👋{Colors.ENDC}")
        sys.exit(0)
    
    else:
        print(f"{Colors.WARNING}Invalid choice. Please run the script again.{Colors.ENDC}")


if __name__ == "__main__":
    main()
