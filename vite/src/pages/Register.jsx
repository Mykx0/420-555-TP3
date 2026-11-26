import { useState } from "react";
import { useNavigate } from "react-router-dom";
import api from "../api.js";
import { useAuth } from "../AuthContext.jsx";


export default function Register() {
  const { login } = useAuth();
  const [form, setForm] = useState({
    name: "",
    pin: "",
    passcode: "",
    confirmPasscode: "",
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.passcode !== form.confirmPasscode) {
      setError("Pass codes do not match.");
      return;
    }
    setError("");
    setLoading(true);

    try {
      const { data } = await api.post("/register", {
        name: form.name,
        pin: form.pin,
        passcode: form.passcode,
      });
      login(data.token);
      navigate("/");
    } catch (err) {
      setError(err.response?.data?.msg || "Could not reach the server.");
    } finally {
      setLoading(false);
    }
  };

  const inputClass =
    "w-full rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500";
  const labelClass = "mb-1 block text-sm font-medium text-gray-700";
  const digits = { inputMode: "numeric", pattern: "\\d{4,6}", minLength: 4, maxLength: 6 };

  return (
    <div className="flex min-h-[70vh] items-center justify-center px-4">
      <form
        onSubmit={handleSubmit}
        className="w-full max-w-sm space-y-4 rounded-lg bg-white p-6 shadow"
      >
        <h2 className="text-2xl font-bold text-gray-900">Register</h2>

        <div>
          <label htmlFor="name" className={labelClass}>Enter your name</label>
          <input id="name" name="name" type="text" required
            value={form.name} onChange={handleChange} className={inputClass} />
        </div>

        <div>
          <label htmlFor="pin" className={labelClass}>Enter a 4 to 6 digit PIN</label>
          <input id="pin" name="pin" type="text" required {...digits}
            placeholder="123456" value={form.pin} onChange={handleChange} className={inputClass} />
        </div>

        <div>
          <label htmlFor="passcode" className={labelClass}>Enter a 4 to 6 digit pass code</label>
          <input id="passcode" name="passcode" type="password" required {...digits}
            placeholder="123456" value={form.passcode} onChange={handleChange} className={inputClass} />
        </div>

        <div>
          <label htmlFor="confirmPasscode" className={labelClass}>Confirm your pass code</label>
          <input id="confirmPasscode" name="confirmPasscode" type="password" required {...digits}
            placeholder="123456" value={form.confirmPasscode} onChange={handleChange} className={inputClass} />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <button type="submit" disabled={loading}
          className="w-full rounded-md bg-indigo-600 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50">
          {loading ? "Creating..." : "Create account"}
        </button>
      </form>
    </div>
  );
}