import sys

def check_gmail():
    with open('backend/core/gmail_oauth_plugin.py', 'r', encoding='utf-8') as f:
        print(f.read()[-1000:])
        
check_gmail()
