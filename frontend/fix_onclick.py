import re
with open(r'd:\GOOGLE PROJECT\frontend\src\TaskAdaptiveWorkspace.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = re.sub(r'onClick=\{\(\) => \{\}\} // "(.*?)"', r'onClick={() => {}} /* \1 */', text)
text = text.replace('onClick={() => {}} // "', 'onClick={() => {}}')
with open(r'd:\GOOGLE PROJECT\frontend\src\TaskAdaptiveWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
