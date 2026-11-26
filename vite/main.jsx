import React from 'react'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './src/App.jsx'
import { AuthProvider } from "./src/AuthContext.jsx";

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <App/>    
      </BrowserRouter>
    </AuthProvider>
  </StrictMode>,
)
