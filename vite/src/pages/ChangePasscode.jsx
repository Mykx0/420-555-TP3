import { useState } from "react";
import api from "../api.js";

export default function ChangePasscode() {
  const [form, setForm] = useState({ current: "", new: "", confirm: "" });
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");

    if (form.new !== form.confirm) {
      setError("The new passcodes do not match.");
      return;
    }

    setLoading(true);
    try {
      const { data } = await api.post("/change-passcode", {
        current: form.current,
        new: form.new,
      });
      setSuccess(data.msg === "passcode updated" ? "Passcode updated." : data.msg);
      setForm({ current: "", new: "", confirm: "" });
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
        <h2 className="text-2xl font-bold text-gray-900">Change passcode</h2>

        <div>
          <label htmlFor="current" className={labelClass}>Current passcode</label>
          <input id="current" name="current" type="password" required {...digits}
            value={form.current} onChange={handleChange} className={inputClass} />
        </div>

        <div>
          <label htmlFor="new" className={labelClass}>New passcode (4 to 6 digits)</label>
          <input id="new" name="new" type="password" required {...digits}
            value={form.new} onChange={handleChange} className={inputClass} />
        </div>

        <div>
          <label htmlFor="confirm" className={labelClass}>Confirm new passcode</label>
          <input id="confirm" name="confirm" type="password" required {...digits}
            value={form.confirm} onChange={handleChange} className={inputClass} />
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}
        {success && <p className="text-sm text-green-600">{success}</p>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-indigo-600 py-2 font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Saving..." : "Change passcode"}
        </button>
      </form>
    </div>
  );
}