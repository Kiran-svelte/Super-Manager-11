import re

with open(r'C:\Users\kiran\Downloads\super_manager_redesign.html', 'r', encoding='utf-8') as f:
    content = f.read()

css_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
if css_match:
    with open(r'd:\GOOGLE PROJECT\frontend\src\SparkLayout.css', 'w', encoding='utf-8') as f:
        f.write(css_match.group(1).strip())

html_match = re.search(r'</style>\s*(.*?)</body>', content, re.DOTALL)
if html_match:
    html = html_match.group(1).strip()
    
    # conversions
    html = html.replace('class=', 'className=')
    html = re.sub(r'onclick="[^"]*"', '', html)
    html = html.replace('<br>', '<br />')
    html = html.replace('<hr>', '<hr />')
    html = re.sub(r'<input([^>]*?)>', r'<input\1 />', html)
    html = html.replace('/> />', '/>')
    html = re.sub(r'style="[^"]*"', '', html)
    html = html.replace('<!--', '{/*').replace('-->', '*/}')
    
    script_match = re.search(r'<script>(.*?)</script>', html, re.DOTALL | re.IGNORECASE)
    if script_match:
        html = html.replace(script_match.group(0), '')
        
    jsx_code = f'''import React, {{ useState }} from "react";
import "./SparkLayout.css";

export default function SparkLayout() {{
  const [activeMode, setActiveMode] = useState("code"); // 'code', 'meeting', 'chat'

  return (
    <>
      {html}
    </>
  );
}}
'''

    with open(r'd:\GOOGLE PROJECT\frontend\src\SparkLayout.jsx', 'w', encoding='utf-8') as f:
        f.write(jsx_code)
        
    print("Done")
