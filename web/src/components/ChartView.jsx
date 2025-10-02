import React from "react";
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend,
  LineChart, Line, PieChart, Pie, Cell
} from "recharts";

/**
 * Expects one of:
 *  - { type: "bar"|"line", data: [{label, value}, ...], xKey?, yKey? }
 *  - { type: "pie", data: [{label, value}, ...] }
 *  - Or a plain array of {label, value}
 */
export default function ChartView({ spec }) {
  if (!spec) return null;

  let type = spec.type || "bar";
  let data = spec.data || spec;
  const xKey = spec.xKey || "label";
  const yKey = spec.yKey || "value";

  // Basic normalization
  if (!Array.isArray(data)) return <div className="text-slate-300">No chartable data.</div>;

  if (type === "pie") {
    return (
      <div className="h-72">
        <ResponsiveContainer>
          <PieChart>
            <Pie dataKey={yKey} nameKey={xKey} data={data} cx="50%" cy="50%" outerRadius={95} label>
              {data.map((_, i) => <Cell key={i} />)}
            </Pie>
            <Legend />
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    );
  }

  if (type === "line") {
    return (
      <div className="h-72">
        <ResponsiveContainer>
          <LineChart data={data}>
            <XAxis dataKey={xKey} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={yKey} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    );
  }

  // default bar
  return (
    <div className="h-72">
      <ResponsiveContainer>
        <BarChart data={data}>
          <XAxis dataKey={xKey} />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey={yKey} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
