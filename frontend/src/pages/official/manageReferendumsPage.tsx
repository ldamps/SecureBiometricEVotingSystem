import React, { useState, useEffect, useCallback } from "react";
import { useTheme } from "../../styles/ThemeContext";
import {
  getPageContentWrapperStyle,
  getPageTitleStyle,
  getCardStyle,
  getCardTextStyle,
  getCardTitleStyle,
  getTabButtonStyle,
  getTableStyle,
  getTableHeaderStyle,
  getTableCellStyle,
  getStatusBadgeStyle,
} from "../../styles/ui";
import type { StatusBadgeVariant } from "../../styles/ui";
import { ReferendumApiRepository } from "../../features/referendum/repositories/referendum-api.repository";
import { Referendum, ReferendumStatus, UpdateReferendumRequest } from "../../features/referendum/model/referendum.model";
import CreateReferendum from "../../features/referendum/components/createReferendum";
import EditReferendum from "../../features/referendum/components/editReferendum";

const referendumApiRepository = new ReferendumApiRepository();

function formatDate(iso: string | undefined): string {
  if (!iso) return "\u2014";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

function statusToBadge(s: string): StatusBadgeVariant {
  if (s === "DRAFT") return "pending";
  if (s === "OPEN") return "open";
  if (s === "CLOSED") return "resolved";
  return "mismatch";
}

const ManageReferendumsPage: React.FC = () => {
  const { theme } = useTheme();

  const [referendums, setReferendums] = useState<Referendum[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [editReferendum, setEditReferendum] = useState<Referendum | null>(null);

  const loadData = useCallback(() => {
    setLoading(true);
    setError(null);
    referendumApiRepository.listReferendums()
      .then(setReferendums)
      .catch((err: Error) => setError(err.message || "Failed to load referendums."))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleStatusChange = async (referendumId: string, newStatus: ReferendumStatus) => {
    try {
      const body: UpdateReferendumRequest = { status: newStatus };
      await referendumApiRepository.updateReferendum(referendumId, body);
      loadData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update referendum status.";
      setError(message);
    }
  };

  const pageWrapper = getPageContentWrapperStyle(theme);
  const pageTitle = getPageTitleStyle(theme);
  const card = getCardStyle(theme);
  const cardTitle = getCardTitleStyle(theme);
  const cardText = getCardTextStyle(theme);

  const handleCreated = () => {
    setCreateOpen(false);
    loadData();
  };

  return (
    <div style={pageWrapper}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: theme.spacing.sm, paddingLeft: theme.spacing.xl, paddingRight: theme.spacing.xl }}>
        <h1 style={{ ...pageTitle, marginBottom: 0, paddingLeft: 0 }}>Manage referendums</h1>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          style={{
            ...getTabButtonStyle(theme, true),
            background: theme.colors.primary,
            color: theme.colors.text.inverse,
          }}
        >
          + New referendum
        </button>
      </div>

      <div style={{ padding: theme.spacing.xl }}>
        {loading && <p style={{ ...cardText, color: theme.colors.text.secondary }}>Loading...</p>}
        {error && (
          <div style={{ ...card, borderLeft: `4px solid ${theme.colors.status.error}`, marginBottom: theme.spacing.lg }}>
            <p style={{ ...cardText, margin: 0, color: theme.colors.status.error }}>{error}</p>
            <button type="button" onClick={loadData} style={{ ...getTabButtonStyle(theme, false), marginTop: theme.spacing.sm, fontSize: theme.fontSizes.sm }}>
              Retry
            </button>
          </div>
        )}

        {!loading && !error && (
          <div style={{ ...card }}>
            <h3 style={{ ...cardTitle, marginBottom: theme.spacing.md }}>Referendums ({referendums.length})</h3>
            {referendums.length === 0 ? (
              <p style={{ ...cardText, fontStyle: "italic" }}>No referendums have been created yet.</p>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={getTableStyle(theme)}>
                  <thead>
                    <tr>
                      <th style={getTableHeaderStyle(theme)}>Title</th>
                      <th style={getTableHeaderStyle(theme)}>Question</th>
                      <th style={getTableHeaderStyle(theme)}>Scope</th>
                      <th style={getTableHeaderStyle(theme)}>Status</th>
                      <th style={getTableHeaderStyle(theme)}>Voting opens</th>
                      <th style={getTableHeaderStyle(theme)}>Voting closes</th>
                      <th style={getTableHeaderStyle(theme)}>Constituencies</th>
                      <th style={getTableHeaderStyle(theme)}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {referendums.map((ref) => (
                      <tr key={ref.id}>
                        <td style={getTableCellStyle(theme)}>{ref.title}</td>
                        <td style={{ ...getTableCellStyle(theme), fontSize: theme.fontSizes.sm, maxWidth: 300, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                          {ref.question}
                        </td>
                        <td style={getTableCellStyle(theme)}>{ref.scope}</td>
                        <td style={getTableCellStyle(theme)}>
                          <span style={getStatusBadgeStyle(theme, statusToBadge(ref.status))}>
                            {ref.status}
                          </span>
                        </td>
                        <td style={{ ...getTableCellStyle(theme), fontSize: theme.fontSizes.sm }}>{formatDate(ref.voting_opens)}</td>
                        <td style={{ ...getTableCellStyle(theme), fontSize: theme.fontSizes.sm }}>{formatDate(ref.voting_closes)}</td>
                        <td style={getTableCellStyle(theme)}>{ref.constituency_ids.length}</td>
                        <td style={{ ...getTableCellStyle(theme), whiteSpace: "nowrap" }}>
                          <div style={{ display: "flex", gap: theme.spacing.xs, flexWrap: "wrap" }}>
                            {ref.status === ReferendumStatus.DRAFT && (
                              <>
                                <button type="button" onClick={() => setEditReferendum(ref)}
                                  style={{ ...getTabButtonStyle(theme, true), background: theme.colors.primary, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                  Edit
                                </button>
                                <button type="button" onClick={() => handleStatusChange(ref.id, ReferendumStatus.OPEN)}
                                  style={{ ...getTabButtonStyle(theme, true), background: theme.colors.status.success, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                  Publish
                                </button>
                              </>
                            )}
                            {ref.status === ReferendumStatus.OPEN && (
                              <>
                                <button type="button" onClick={() => handleStatusChange(ref.id, ReferendumStatus.CLOSED)}
                                  style={{ ...getTabButtonStyle(theme, false), padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                  Close
                                </button>
                                <button type="button" onClick={() => handleStatusChange(ref.id, ReferendumStatus.DRAFT)}
                                  style={{ ...getTabButtonStyle(theme, false), padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                  Revert to draft
                                </button>
                              </>
                            )}
                            {ref.status === ReferendumStatus.CLOSED && (
                              <button type="button" onClick={() => handleStatusChange(ref.id, ReferendumStatus.OPEN)}
                                style={{ ...getTabButtonStyle(theme, true), background: theme.colors.status.success, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                Reopen
                              </button>
                            )}
                            {ref.status !== ReferendumStatus.CANCELLED && (
                              <button type="button" onClick={() => handleStatusChange(ref.id, ReferendumStatus.CANCELLED)}
                                style={{ ...getTabButtonStyle(theme, false), background: theme.colors.status.error, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                Cancel
                              </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>

      <CreateReferendum
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={handleCreated}
      />
      <EditReferendum
        open={editReferendum !== null}
        referendum={editReferendum}
        onClose={() => setEditReferendum(null)}
        onUpdated={() => { setEditReferendum(null); loadData(); }}
      />
    </div>
  );
};

export default ManageReferendumsPage;
