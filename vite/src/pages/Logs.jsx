import { useEffect, useState, useCallback } from "react";
import api from "../api.js";

const levelStyles = {
  INFO: "bg-blue-100 text-blue-800",
  WARNING: "bg-yellow-100 text-yellow-800",
  ERROR: "bg-red-100 text-red-800",
};

export default function Logs() {
  const [logs, setLogs] = useState([]);
  const [level, setLevel] = useState("ALL");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get("/logs");
      setLogs(data);
    } catch (err) {
      setError(
        err.response?.status === 401
          ? "You must be logged in to view the logs."
          : err.response?.data?.msg || "Could not load the logs."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const filtered = logs.filter(
    (l) =>
      (level === "ALL" || l.level === level) &&
      `${l.action} ${l.message}`.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="mx-auto max-w-5xl px-4 py-8">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <h2 className="mr-auto text-2xl font-bold text-white-900">Activity logs</h2>

        <input
          type="text"
          placeholder="Search action or message..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm text-white-900 focus:border-indigo-500 focus:outline-none focus:ring-1 focus:ring-indigo-500"
        />

        <select
          value={level}
          onChange={(e) => setLevel(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-2 text-sm text-white-900"
        >
          <option value="ALL">All levels</option>
          <option value="INFO">Info</option>
          <option value="WARNING">Warning</option>
          <option value="ERROR">Error</option>
        </select>

        <button
          onClick={load}
          disabled={loading}
          className="rounded-md bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

      <div className="overflow-x-auto rounded-lg bg-white shadow">
        <table className="w-full text-left text-sm">
          <thead className="bg-gray-50 text-xs uppercase text-gray-500">
            <tr>
              <th className="px-4 py-3">Timestamp</th>
              <th className="px-4 py-3">Level</th>
              <th className="px-4 py-3">Action</th>
              <th className="px-4 py-3">Message</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100 text-gray-700">
            {filtered.map((l) => (
              <tr key={l.timestamp}>
                <td className="whitespace-nowrap px-4 py-2 font-mono text-xs">
                  {l.timestamp}
                </td>
                <td className="px-4 py-2">
                  <span
                    className={`rounded px-2 py-0.5 text-xs font-medium ${
                      levelStyles[l.level] || "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {l.level}
                  </span>
                </td>
                <td className="px-4 py-2 font-medium">{l.action}</td>
                <td className="px-4 py-2">{l.message}</td>
              </tr>
            ))}
            {!loading && filtered.length === 0 && (
              <tr>
                <td colSpan={4} className="px-4 py-6 text-center text-gray-500">
                  No logs to show.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <p className="mt-2 text-xs text-gray-500">
        Showing {filtered.length} of {logs.length} entries, newest first.
      </p>
    </div>
  );
}