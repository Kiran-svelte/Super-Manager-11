import os

with open(r'd:\GOOGLE PROJECT\frontend\src\App.jsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("import UIComponentRenderer from './components/UIComponentRenderer'", "import UIComponentRenderer from './components/UIComponentRenderer'\nimport HumanFallback from './components/HumanFallback'")

target = "{m.ui_components && <div className=\"msg-ui-components\"><UIComponentRenderer component={m.ui_components} onAction={handleAction} onMessage={send} loading={loading} /></div>}"

fallback_render = target + """
                        {m.steps && m.steps.some(s => s.name === 'human_fallback') && (
                          <div className=\"msg-ui-components\">
                            <HumanFallback 
                              data={m.steps.find(s => s.name === 'human_fallback').data} 
                              onComplete={() => send('I have completed the manual steps. Please proceed.')} 
                              onDismiss={() => send('I cannot complete these steps right now.')} 
                            />
                          </div>
                        )}
                        {m.type === 'human_fallback' && m.context && (
                          <div className=\"msg-ui-components\">
                            <HumanFallback 
                              data={{context: m.context}} 
                              onComplete={() => send('I have completed the manual steps. Please proceed.')} 
                              onDismiss={() => send('I cannot complete these steps right now.')} 
                            />
                          </div>
                        )}
"""

content = content.replace(target, fallback_render)

with open(r'd:\GOOGLE PROJECT\frontend\src\App.jsx', 'w', encoding='utf-8') as f:
    f.write(content)
