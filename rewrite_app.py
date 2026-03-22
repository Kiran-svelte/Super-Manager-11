import os
import re

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    orig = f.read()

import_statement = "import TaskAdaptiveWorkspace from './TaskAdaptiveWorkspace'\n"

# add import if not there
if "TaskAdaptiveWorkspace" not in orig:
    orig = orig.replace("import './App.css'", "import './App.css'\n" + import_statement)

match = re.search(r'return\s*\(\s*<div className="super-app">.*?}\n\s*export default App', orig, re.DOTALL)

if match:
    new_return = '''return (
    <TaskAdaptiveWorkspace 
      messages={messages}
      input={input}
      setInput={setInput}
      send={send}
      loading={loading}
      AgentSteps={AgentSteps}
      UIComponentRenderer={UIComponentRenderer}
      sessionId={sessionId}
    />
  )
}

export default App
'''
    new_content = orig[:match.start()] + new_return
    with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced App.jsx return correctly")
else:
    print("Could not find start of App return.")
