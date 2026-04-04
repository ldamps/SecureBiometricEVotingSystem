import React from "react";
import { PieChart, Pie, Cell, Legend, Tooltip, ResponsiveContainer } from "recharts";
import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle, getCardTitleStyle } from "../../../styles/ui";

export interface SeatAllocationItem {
  party: string;
  seats: number;
  fill: string;
}

interface SeatAllocationChartProps {
  data: SeatAllocationItem[];
  title?: string;
  height?: number;
}

const SeatAllocationChart: React.FC<SeatAllocationChartProps> = ({
  data,
  title = "Seat allocation",
  height = 260,
}) => {
  const { theme } = useTheme();
  const card = getCardStyle(theme);
  const cardTitle = getCardTitleStyle(theme);

  return (
    <div style={card}>
      <h3 style={{ ...cardTitle, marginBottom: theme.spacing.md }}>{title}</h3>
      <div style={{ width: "100%", height }}>
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie
              data={data}
              dataKey="seats"
              nameKey="party"
              cx="50%"
              cy="50%"
              outerRadius={80}
              label={({ name, value }) => `${name}: ${value}`}
            >
              {data.map((_, i) => (
                <Cell key={i} fill={data[i].fill} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{ background: theme.colors.surface, border: `1px solid ${theme.colors.border}` }}
              formatter={(value: unknown) => [value, "Seats"] as [React.ReactNode, string]}
            />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
};

export default SeatAllocationChart;
