import re

with open(r'd:\GOOGLE PROJECT\frontend\src\SparkLayout.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

# We only want to replace { and } inside the returned JSX, specifically inside the code viewer.
# Let's find all `{` and `}` that are followed by spaces or text except when they are part of `{/*` or `*/}` or inside our custom JSX component logic (which we don't have much of in the HTML block yet).
text = text.replace('{ origin: process.env.ALLOWED_ORIGINS }', '&#123; origin: process.env.ALLOWED_ORIGINS &#125;')
text = text.replace('{ windowMs: 15 * 60 * 1000, max: 100 }', '&#123; windowMs: 15 * 60 * 1000, max: 100 &#125;')
text = text.replace('{ return res.status(200).json({ status: \'ok\' }); }', '&#123; return res.status(200).json(&#123; status: \'ok\' &#125;); &#125;')

# Brute force replace known code span sequences
text = text.replace('({ ', '(&#123; ')
text = text.replace(' })', ' &#125;)')
text = text.replace(' { ', ' &#123; ')
text = text.replace(' } ', ' &#125; ')
text = text.replace(' }<', ' &#125;<')
text = text.replace('>{ ', '>&#123; ')

with open(r'd:\GOOGLE PROJECT\frontend\src\SparkLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
    
print("Replaced")
