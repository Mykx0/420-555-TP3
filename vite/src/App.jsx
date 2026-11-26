import { Routes, Route, Link, useNavigate } from "react-router-dom";
import Login from "./pages/Login.jsx";
import Register from "./pages/Register.jsx";
import Logs from "./pages/Logs.jsx";
import RequireAuth from "./RequireAuth.jsx";
import { useAuth } from "./AuthContext.jsx";
import "./App.css";

function App() {
  const { isLoggedIn, logout } = useAuth();   // inside the component
  const navigate = useNavigate();             // inside the component

  return (
    <>
      <header className="bg-white shadow">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
          <Link to="/" className="text-xl font-bold text-indigo-600">TP3</Link>

          <nav className="flex items-center gap-3">
            {isLoggedIn ? (
              <>
                <Link to="/logs" className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100">
                  Logs
                </Link>
                <button
                  onClick={() => { logout(); navigate("/login"); }}
                  className="rounded-md bg-gray-800 px-4 py-2 text-sm font-medium text-white hover:bg-gray-900"
                >
                  Logout
                </button>
              </>
            ) : (
              <>
                <Link to="/login" className="rounded-md px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-100">
                  Login
                </Link>
                <Link to="/register" className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700">
                  Register
                </Link>
              </>
            )}
          </nav>
        </div>
      </header>

      <Routes>
        <Route path="/" element={<h1 className="mt-8 text-center text-3xl font-bold">TP3 d'objets connectés</h1>} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/logs" element={<RequireAuth><Logs /></RequireAuth>} />
      </Routes>
    </>
  );
}

export default App;