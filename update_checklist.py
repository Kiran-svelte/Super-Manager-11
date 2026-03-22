import sys

def update_checklist():
    with open('checklist.md', 'r', encoding='utf-8') as f:
        c = f.read()

    replacements = [
        ("[ ] Backend: FastAPI", "[x] Backend: FastAPI"),
        ("[ ] AI Provider Config: OpenAI", "[x] AI Provider Config: OpenAI"),
        ("[ ] AI Provider Config: Gemini", "[x] AI Provider Config: Gemini"),
        ("[ ] Database: Supabase", "[x] Database: Supabase"),
        ("[ ] Security: AES", "[x] Security: AES"),
        ("[ ] Design DB Schema for", "[x] Design DB Schema for"),
        ("[ ] API Route: `GET /api/integrations/status`", "[x] API Route: `GET /api/integrations/status`"),
        ("[ ] API Route: `POST /api/integrations/connect`", "[x] API Route: `POST /api/integrations/connect`"),
        ("[ ] API Route: `GET /api/integrations/callback`", "[x] API Route: `GET /api/integrations/callback`"),
        ("[ ] API Route: `POST /api/integrations/revoke`", "[x] API Route: `POST /api/integrations/revoke`"),
        ("[ ] Fallback Routing Logic", "[x] Fallback Routing Logic"),
        ("[ ] Token Validation & Auto-refresh logic.", "[x] Token Validation & Auto-refresh logic.")
    ]
    
    for old, new in replacements:
        c = c.replace(old, new)
        
    with open('checklist.md', 'w', encoding='utf-8') as f:
        f.write(c)

if __name__ == '__main__':
    update_checklist()
