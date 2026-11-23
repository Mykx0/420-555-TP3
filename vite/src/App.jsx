import React from 'react'
import './App.css'

function App() {
  return (
    <>
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <span className="text-xl font-bold text-indigo-600">TP3</span>

          <nav className="flex items-center gap-3">
            <a
              href="/login"
              className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100"
            >
              Login
            </a>
            <a
              href="/register"
              className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700"
            >
              Register
            </a>
          </nav>
        </div>
      </header>

      <h1 className="mt-8 text-center text-3xl font-bold">
        TP3 d'objets connectés
      </h1>
    </>
  )
}

export default App