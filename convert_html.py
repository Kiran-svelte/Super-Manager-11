import os
import re

html_path = r'C:\Users\kiran\Downloads\super_manager_task_adaptive_workspaces (1).html'
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()

# Convert basic HTML to JSX
html = html.replace('class="', 'className="')
html = html.replace('onclick="switchTask', 'data-action="switchTask')
html = html.replace('onclick="', 'onClick={() => {}} // "')

def style_replacer(m):
    css = m.group(1)
    new_styles = []
    for decl in css.split(';'):
        if ':' in decl:
            k, v = decl.split(':', 1)
            k = k.strip()
            v = v.strip()
            # camelCase conversion for keys like 'align-items'
            parts = k.split('-')
            k_camel = parts[0] + ''.join(p.capitalize() for p in parts[1:])
            new_styles.append(f"{k_camel}: '{v}'")
    return "style={{" + ", ".join(new_styles) + "}}"

html = re.sub(r'style="(.*?)"', style_replacer, html)
html = html.replace('<!--', '{/*').replace('-->', '*/}')
html = html.replace('<br>', '<br />').replace('<hr>', '<hr />').replace('<img>', '<img />')

# Just get everything inside <div className="app">
match = re.search(r'<div className="app">(.*?)</div>\s*<script>', html, re.DOTALL)
if match:
    app_html = '<div className="app">' + match.group(1) + '</div>'
else:
    app_html = '<div>Error extracting app</div>'

# Extract styles
style_match = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
if style_match:
    with open(r'd:\GOOGLE PROJECT\frontend\src\TaskWorkspace.css', 'w', encoding='utf-8') as f:
        f.write(style_match.group(1).replace('body {', 'body2 {').replace('margin: 0;', '').replace('padding: 0;', ''))

jsx_content = f'''import React, {{ useState, useEffect }} from "react";
import "./TaskWorkspace.css";

export default function TaskAdaptiveWorkspace() {{
  return (
    {app_html}
  );
}}
'''

# fix unmatched tags
jsx_content = jsx_content.replace('<img src="https://i.pravatar.cc/100?img=68" className="author-img">', '<img src="https://i.pravatar.cc/100?img=68" className="author-img" />')
jsx_content = jsx_content.replace('<img src="https://i.pravatar.cc/100?img=47" className="author-img">', '<img src="https://i.pravatar.cc/100?img=47" className="author-img" />')
jsx_content = jsx_content.replace('<input type="checkbox" checked>', '<input type="checkbox" defaultChecked />')
jsx_content = jsx_content.replace('<input type="checkbox">', '<input type="checkbox" />')
jsx_content = jsx_content.replace('<input type="text" value="BOM - SFO" className="ts-select">', '<input type="text" defaultValue="BOM - SFO" className="ts-select" />')
jsx_content = jsx_content.replace('<input type="text" placeholder="Type your message...">', '<input type="text" placeholder="Type your message..." />')
jsx_content = jsx_content.replace('onClick={() => {}} // "switchTask', 'onClick={() => {}} // "')


with open(r'd:\GOOGLE PROJECT\frontend\src\TaskAdaptiveWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(jsx_content)

print('Success')