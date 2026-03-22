import os

with open('frontend/src/App.jsx', 'r', encoding='utf-8') as f:
    orig = f.read()

import_statement = "import TaskAdaptiveWorkspace from './TaskAdaptiveWorkspace'\n"

# add import if not there
if "TaskAdaptiveWorkspace" not in orig:
    orig = orig.replace("import './App.css'", "import './App.css'\n" + import_statement)

# find the return of App
# we know it's function App() and has return ( <div className="super-app">
idx = orig.find('return (\n      <div className="super-app">')
if idx == -1:
    idx = orig.find('return (\n    <div className="super-app">')
if idx == -1:
    idx = orig.find('return (\n    <div')

if idx != -1:
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
    new_content = orig[:idx] + new_return
    with open('frontend/src/App.jsx', 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Replaced App.jsx return")
else:
    print("Could not find start of App return.")

