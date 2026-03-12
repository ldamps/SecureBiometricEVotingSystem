import React, { useState } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import {
  getSectionH2Style,
  getCardStyle,
  getCardTextStyle,
  getTabButtonStyle,
  getTableStyle,
  getTableHeaderStyle,
  getTableCellStyle,
  getStatusBadgeStyle,
} from "../../../styles/ui";
import AddOfficial, { type NewOfficialData } from "./add_official";

// --- Mock data ---

type OfficialStatus = "ok" | "pending" | "mismatch";

interface ElectionOfficial {
  id: string;
  firstName: string;
  lastName: string;
  email: string;
  accessLevel: string;
  status: OfficialStatus;
}

const MOCK_OFFICIALS: ElectionOfficial[] = [
  { id: "off-1", firstName: "Margaret", lastName: "Clarke", email: "m.clarke@electoral.gov.uk", accessLevel: "Returning Officer", status: "ok" },
  { id: "off-2", firstName: "James", lastName: "Patel", email: "j.patel@electoral.gov.uk", accessLevel: "Presiding Officer", status: "ok" },
  { id: "off-3", firstName: "Anya", lastName: "Kowalski", email: "a.kowalski@electoral.gov.uk", accessLevel: "Poll Clerk", status: "pending" },
  { id: "off-4", firstName: "David", lastName: "Osei", email: "d.osei@electoral.gov.uk", accessLevel: "Electoral Registration Officer", status: "ok" },
];

const STATUS_LABELS: Record<OfficialStatus, string> = {
  ok: "Active",
  pending: "Pending setup",
  mismatch: "Revoked",
};

const ManageOfficials: React.FC = () => {
  const { theme } = useTheme();
  const [officials, setOfficials] = useState<ElectionOfficial[]>(MOCK_OFFICIALS);
  const [addModalOpen, setAddModalOpen] = useState(false);

  const sectionH2 = getSectionH2Style(theme);
  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);

  const handleAdd = (data: NewOfficialData) => {
    const newOfficial: ElectionOfficial = {
      id: `off-${Date.now()}`,
      firstName: data.firstName,
      lastName: data.lastName,
      email: data.email,
      accessLevel: data.accessLevel,
      status: "pending",
    };
    setOfficials((prev) => [...prev, newOfficial]);
    setAddModalOpen(false);
  };


  const handleOffboard = (id: string) => {
    setOfficials((prev) => prev.filter((o) => o.id !== id));
  };

  return (
    <section>
      <h2 style={sectionH2}>Manage officials</h2>
      <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
        Add, manage, and revoke access for election officials. Officials with a pending status have not yet completed their biometric setup.
      </p>

      <div style={card}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: theme.spacing.sm,
            marginBottom: theme.spacing.md,
          }}
        >
          <span style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary }}>
            {officials.length} official{officials.length !== 1 ? "s" : ""}
          </span>
          <button
            type="button"
            onClick={() => setAddModalOpen(true)}
            style={{
              ...getTabButtonStyle(theme, true),
              background: theme.colors.primary,
              color: theme.colors.text.inverse,
            }}
          >
            + Add official
          </button>
        </div>

        {officials.length === 0 ? (
          <p style={{ ...cardText, fontStyle: "italic" }}>No officials added yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={getTableStyle(theme)}>
              <thead>
                <tr>
                  <th style={getTableHeaderStyle(theme)}>First name</th>
                  <th style={getTableHeaderStyle(theme)}>Email</th>
                  <th style={getTableHeaderStyle(theme)}>Access level</th>
                  <th style={getTableHeaderStyle(theme)}>Status</th>
                  <th style={getTableHeaderStyle(theme)}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {officials.map((official) => {
                  return (
                    <tr key={official.id}>
                      <td style={getTableCellStyle(theme)}>{official.firstName}</td>
                      <td style={getTableCellStyle(theme)}>{official.email}</td>
                      <td style={getTableCellStyle(theme)}>{official.accessLevel}</td>
                      <td style={getTableCellStyle(theme)}>
                        <span style={getStatusBadgeStyle(theme, official.status)}>
                          {STATUS_LABELS[official.status]}
                        </span>
                      </td>
                      <td style={getTableCellStyle(theme)}>
                        <button
                          type="button"
                          onClick={() => handleOffboard(official.id)}
                          style={{
                                ...getTabButtonStyle(theme, false),
                                padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                                fontSize: theme.fontSizes.xs,
                                color: theme.colors.status.error,
                           }}
                        >
                          Offboard
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <AddOfficial
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        onAdd={handleAdd}
      />
    </section>
  );
};

export default ManageOfficials;
