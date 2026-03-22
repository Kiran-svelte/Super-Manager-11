import re

with open(r'd:\GOOGLE PROJECT\frontend\src\SparkLayout_raw.html', 'r', encoding='utf-8') as f:
    html = f.read()

# basic HTML to JSX conversions
html = html.replace('class=', 'className=')
html = re.sub(r'onclick="[^"]*"', '', html)
html = html.replace('<br>', '<br />')
html = html.replace('<hr>', '<hr />')
# Fix input tags not closed
html = re.sub(r'<input([^>]*?)>', r'<input\1 />', html)
# If it resulted in <input ... /> />, we can fix it:
html = html.replace('/> />', '/>')

# Remove inline styles for React porting simplicity
html = re.sub(r'style="[^"]*"', '', html)
html = html.replace('<!--', '{/*').replace('-->', '*/}')

# We need to drop the inline script section at the bottom so it doesn't break JSX
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

print("Conversion complete.")
