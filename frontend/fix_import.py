with open(r'd:\GOOGLE PROJECT\frontend\src\SparkLayout.jsx', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('import React, &#123; useState &#125; from "react";', 'import React, { useState } from "react";')

with open(r'd:\GOOGLE PROJECT\frontend\src\SparkLayout.jsx', 'w', encoding='utf-8') as f:
    f.write(text)
