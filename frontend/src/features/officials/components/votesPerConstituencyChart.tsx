import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";
import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle, getCardTitleStyle } from "../../../styles/ui";

export interface ConstituencyChartItem {
  id: string;
  name: string;
  votesCast: number;
}

interface VotesPerConstituencyChartProps {
  data: ConstituencyChartItem[];
  title?: string;
  height?: number;
}

const VotesPerConstituencyChart: React.FC<VotesPerConstituencyChartProps> = ({
  data,
  title = "Votes per constituency",
  height = 260,
}) => {
  const { theme } = useTheme();
  const card = getCardStyle(theme);
  const cardTitle = getCardTitleStyle(theme);

  const chartData = data.map((c) => ({
    name: c.name.length > 14 ? c.name.slice(0, 12) + "…" : c.name,
    fullName: c.name,
    votes: c.votesCast,
  }));

  return (
    <div style={card}>
      <h3 style={{ ...cardTitle, marginBottom: theme.spacing.md }}>{title}</h3>
      {data.length === 0 ? (
        <p style={{ color: theme.colors.text.secondary, fontSize: theme.fontSizes.sm, fontStyle: "italic" }}>
          No constituency data available.
        </p>
      ) : (
        <div style={{ width: "100%", height }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: theme.colors.text.secondary }} />
              <YAxis tick={{ fontSize: 11, fill: theme.colors.text.secondary }} />
              <Tooltip
                contentStyle={{ background: theme.colors.surface, border: `1px solid ${theme.colors.border}` }}
                labelStyle={{ color: theme.colors.text.primary }}
                formatter={(value: unknown) =>
                  [typeof value === "number" ? value.toLocaleString() : String(value), "Votes"] as [React.ReactNode, string]
                }
                labelFormatter={(_, payload) =>
                  (payload?.[0] as { payload?: { fullName?: string } })?.payload?.fullName ?? ""
                }
              />
              <Bar dataKey="votes" name="Votes cast" fill={theme.colors.bar} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

export default VotesPerConstituencyChart;
