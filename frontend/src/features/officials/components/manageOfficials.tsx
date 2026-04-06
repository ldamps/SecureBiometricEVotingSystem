import React, { useState, useEffect, useCallback } from "react";
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
import type { StatusBadgeVariant } from "../../../styles/ui";
import AddOfficial, { type NewOfficialData } from "./add_official";
import { OfficialApiRepository } from "../repositories/official-api.repository";
import { Official, OfficialRole } from "../model/official.model";
import { getAccessTokenSubject } from "../../../services/api-client.service";

const officialApiRepository = new OfficialApiRepository();

const ROLE_LABELS: Record<OfficialRole, string> = {
  [OfficialRole.ADMIN]: "Administrator",
  [OfficialRole.OFFICER]: "Election Officer",
};

const ManageOfficials: React.FC = () => {
  const { theme } = useTheme();
  const [officials, setOfficials] = useState<Official[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [actionInProgress, setActionInProgress] = useState<string | null>(null);

  const sectionH2 = getSectionH2Style(theme);
  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);

  const loadOfficials = useCallback(() => {
    setLoading(true);
    setError(null);
    officialApiRepository.listOfficials()
      .then(setOfficials)
      .catch((err: Error) => {
        setError(err.message || "Failed to load officials.");
        setOfficials([]);
      })
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadOfficials(); }, [loadOfficials]);

  const handleAdd = async (data: NewOfficialData) => {
    const currentOfficialId = getAccessTokenSubject();
    await officialApiRepository.createOfficial({
      username: data.email.split("@")[0],
      first_name: data.firstName,
      last_name: data.lastName,
      email: data.email,
      role: OfficialRole.OFFICER,
      created_by: currentOfficialId ?? "",
    });
    setAddModalOpen(false);
    loadOfficials();
  };

  const handleDeactivate = async (id: string) => {
    setActionInProgress(id);
    await officialApiRepository.deactivateOfficial(id)
      .finally(() => setActionInProgress(null));
    loadOfficials();
  };

  const handleActivate = async (id: string) => {
    setActionInProgress(id);
    await officialApiRepository.activateOfficial(id)
      .finally(() => setActionInProgress(null));
    loadOfficials();
  };

  return (
    <section>
      <h2 style={sectionH2}>Manage officials</h2>
      <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
        Add, manage, and deactivate election officials. Use this area to control who has access to the verification dashboard.
      </p>

      {loading && (
        <div style={{ ...card, padding: theme.spacing.xl, textAlign: "center" }}>
          <p style={{ ...cardText, margin: 0, color: theme.colors.text.secondary }}>Loading officials…</p>
        </div>
      )}

      {error && (
        <div style={{ ...card, borderLeft: `4px solid ${theme.colors.status.error}`, marginBottom: theme.spacing.md }}>
          <p style={{ ...cardText, margin: 0, color: theme.colors.status.error }}>{error}</p>
          <button
            type="button"
            onClick={loadOfficials}
            style={{ ...getTabButtonStyle(theme, false), marginTop: theme.spacing.sm, fontSize: theme.fontSizes.sm }}
          >
            Retry
          </button>
        </div>
      )}

      {!loading && !error && (
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
            <p style={{ ...cardText, fontStyle: "italic" }}>No officials found.</p>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={getTableStyle(theme)}>
                <thead>
                  <tr>
                    <th style={getTableHeaderStyle(theme)}>Name</th>
                    <th style={getTableHeaderStyle(theme)}>Username</th>
                    <th style={getTableHeaderStyle(theme)}>Email</th>
                    <th style={getTableHeaderStyle(theme)}>Role</th>
                    <th style={getTableHeaderStyle(theme)}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {officials.map((official) => {
                    const fullName = [official.first_name, official.last_name].filter(Boolean).join(" ") || official.username;
                    return (
                      <tr key={official.id}>
                        <td style={getTableCellStyle(theme)}>{fullName}</td>
                        <td style={getTableCellStyle(theme)}>{official.username}</td>
                        <td style={getTableCellStyle(theme)}>{official.email || "—"}</td>
                        <td style={getTableCellStyle(theme)}>
                          <span style={getStatusBadgeStyle(theme, official.role === OfficialRole.ADMIN ? "ok" : "pending")}>
                            {ROLE_LABELS[official.role]}
                          </span>
                        </td>
                        <td style={getTableCellStyle(theme)}>
                          <button
                            type="button"
                            disabled={actionInProgress === official.id}
                            onClick={() => handleDeactivate(official.id)}
                            style={{
                              ...getTabButtonStyle(theme, false),
                              padding: `${theme.spacing.xs} ${theme.spacing.sm}`,
                              fontSize: theme.fontSizes.xs,
                              color: theme.colors.status.error,
                            }}
                          >
                            {actionInProgress === official.id ? "…" : "Deactivate"}
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
      )}

      <AddOfficial
        open={addModalOpen}
        onClose={() => setAddModalOpen(false)}
        onAdd={handleAdd}
      />
    </section>
  );
};

export default ManageOfficials;
