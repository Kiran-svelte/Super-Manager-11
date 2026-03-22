with open(r'd:\GOOGLE PROJECT\frontend\src\TaskAdaptiveWorkspace.jsx', 'r', encoding='utf-8') as f:
    text = f.read()
text = text.replace('cors({ <span className="nm">origin</span>: process.env.<span className="nm">ORIGINS</span> })', 'cors(&#123; <span className="nm">origin</span>: process.env.<span className="nm">ORIGINS</span> &#125;)')
with open(r'd:\GOOGLE PROJECT\frontend\src\TaskAdaptiveWorkspace.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
