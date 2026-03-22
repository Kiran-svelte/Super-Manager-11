import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import SparkLayout from './SparkLayout'
import TaskAdaptiveWorkspace from './TaskAdaptiveWorkspace'

const RootComponent = TaskAdaptiveWorkspace;

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <RootComponent />
  </React.StrictMode>,
)
