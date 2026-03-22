import sys
with open('backend/routes/tasks_v2.py', 'r', encoding='utf-8') as f: content = f.read()
content = content.replace('user_email: str = \
default@user.com\', 'user_id: str')
content = content.replace('user_email: str', 'user_id: str')
content = content.replace('user_id=user_email', 'user_id=user_id')
content = content.replace('orchestrator.get_user_tasks(user_email, status)', 'orchestrator.get_user_tasks(user_id, status)')
content = content.replace('eq(\
user_id\, user_email)', 'eq(\user_id\, user_id)')
with open('backend/routes/tasks_v2.py', 'w', encoding='utf-8') as f: f.write(content)
