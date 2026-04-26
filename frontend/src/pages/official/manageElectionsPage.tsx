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
import { ElectionApiRepository } from "../../features/election/repositories/election-api.repository";
import { Election, ElectionStatus, ELECTION_TYPE_LABELS, ALLOCATION_METHOD_LABELS, AllocationMethod, ElectionType, UpdateElectionRequest } from "../../features/election/model/election.model";
import CreateElection from "../../features/election/components/createElection";
import EditElection from "../../features/election/components/editElection";
import ReopenWindowModal from "../../features/officials/components/reopenWindowModal";

const electionApiRepository = new ElectionApiRepository();

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

const ManageElectionsPage: React.FC = () => {
  const { theme } = useTheme();

  const [elections, setElections] = useState<Election[]>([]);
  const [hasLoaded, setHasLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [createOpen, setCreateOpen] = useState(false);
  const [editElection, setEditElection] = useState<Election | null>(null);
  const [reopenTarget, setReopenTarget] = useState<Election | null>(null);

  const loadData = useCallback(() => {
    setError(null);
    electionApiRepository.listElections()
      .then(setElections)
      .catch((err: Error) => setError(err.message || "Failed to load elections."))
      .finally(() => setHasLoaded(true));
  }, []);

  useEffect(() => { loadData(); }, [loadData]);

  const handleStatusChange = async (electionId: string, newStatus: ElectionStatus) => {
    try {
      const body: UpdateElectionRequest = { status: newStatus };
      await electionApiRepository.updateElection(electionId, body);
      loadData();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update election status.";
      setError(message);
    }
  };

  const handleReopenConfirm = async (votingOpensIso: string | undefined, votingClosesIso: string) => {
    if (!reopenTarget) return;
    const body: UpdateElectionRequest = {
      status: ElectionStatus.OPEN,
      voting_opens: votingOpensIso,
      voting_closes: votingClosesIso,
    };
    await electionApiRepository.updateElection(reopenTarget.id, body);
    setReopenTarget(null);
    loadData();
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
        <h1 style={{ ...pageTitle, marginBottom: 0, paddingLeft: 0 }}>Manage elections</h1>
        <button
          type="button"
          onClick={() => setCreateOpen(true)}
          style={{
            ...getTabButtonStyle(theme, true),
            background: theme.colors.primary,
            color: theme.colors.text.inverse,
          }}
        >
          + New election
        </button>
      </div>

      <div style={{ padding: theme.spacing.xl }}>
        {!hasLoaded && <p style={{ ...cardText, color: theme.colors.text.secondary }}>Loading...</p>}
        {error && (
          <div style={{ ...card, borderLeft: `4px solid ${theme.colors.status.error}`, marginBottom: theme.spacing.lg }}>
            <p style={{ ...cardText, margin: 0, color: theme.colors.status.error }}>{error}</p>
            <button type="button" onClick={loadData} style={{ ...getTabButtonStyle(theme, false), marginTop: theme.spacing.sm, fontSize: theme.fontSizes.sm }}>
              Retry
            </button>
          </div>
        )}

        {hasLoaded && !error && (
          <div style={{ ...card }}>
            <h3 style={{ ...cardTitle, marginBottom: theme.spacing.md }}>Elections ({elections.length})</h3>
            {elections.length === 0 ? (
              <p style={{ ...cardText, fontStyle: "italic" }}>No elections have been created yet.</p>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table style={getTableStyle(theme)}>
                  <thead>
                    <tr>
                      <th style={getTableHeaderStyle(theme)}>Title</th>
                      <th style={getTableHeaderStyle(theme)}>Type</th>
                      <th style={getTableHeaderStyle(theme)}>System</th>
                      <th style={getTableHeaderStyle(theme)}>Scope</th>
                      <th style={getTableHeaderStyle(theme)}>Status</th>
                      <th style={getTableHeaderStyle(theme)}>Voting opens</th>
                      <th style={getTableHeaderStyle(theme)}>Voting closes</th>
                      <th style={getTableHeaderStyle(theme)}>Constituencies</th>
                      <th style={getTableHeaderStyle(theme)}>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {elections.map((el) => (
                      <tr key={el.id}>
                        <td style={getTableCellStyle(theme)}>{el.title}</td>
                        <td style={{ ...getTableCellStyle(theme), fontSize: theme.fontSizes.sm }}>
                          {ELECTION_TYPE_LABELS[el.election_type as ElectionType] ?? el.election_type}
                        </td>
                        <td style={{ ...getTableCellStyle(theme), fontSize: theme.fontSizes.sm }}>
                          {ALLOCATION_METHOD_LABELS[el.allocation_method as AllocationMethod] ?? el.allocation_method}
                        </td>
                        <td style={getTableCellStyle(theme)}>{el.scope}</td>
                        <td style={getTableCellStyle(theme)}>
                          <span style={getStatusBadgeStyle(theme, statusToBadge(el.status))}>
                            {el.status}
                          </span>
                        </td>
                        <td style={{ ...getTableCellStyle(theme), fontSize: theme.fontSizes.sm }}>{formatDate(el.voting_opens)}</td>
                        <td style={{ ...getTableCellStyle(theme), fontSize: theme.fontSizes.sm }}>{formatDate(el.voting_closes)}</td>
                        <td style={getTableCellStyle(theme)}>{el.constituency_ids.length}</td>
                        <td style={{ ...getTableCellStyle(theme), whiteSpace: "nowrap" }}>
                          <div style={{ display: "flex", gap: theme.spacing.xs, flexWrap: "wrap" }}>
                            {el.status === ElectionStatus.DRAFT && (
                              <>
                                <button type="button" onClick={() => setEditElection(el)}
                                  style={{ ...getTabButtonStyle(theme, true), background: theme.colors.primary, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                  Edit
                                </button>
                                <button type="button" onClick={() => handleStatusChange(el.id, ElectionStatus.OPEN)}
                                  style={{ ...getTabButtonStyle(theme, true), background: theme.colors.status.success, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                  Publish
                                </button>
                              </>
                            )}
                            {el.status === ElectionStatus.OPEN && (
                              <>
                                <button type="button" onClick={() => handleStatusChange(el.id, ElectionStatus.CLOSED)}
                                  style={{ ...getTabButtonStyle(theme, false), padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                  Close
                                </button>
                                <button type="button" onClick={() => handleStatusChange(el.id, ElectionStatus.DRAFT)}
                                  style={{ ...getTabButtonStyle(theme, false), padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                  Revert to draft
                                </button>
                              </>
                            )}
                            {el.status === ElectionStatus.CLOSED && (
                              <button type="button" onClick={() => setReopenTarget(el)}
                                style={{ ...getTabButtonStyle(theme, true), background: theme.colors.status.success, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                                Reopen
                              </button>
                            )}
                            {el.status !== ElectionStatus.CANCELLED && (
                              <button type="button" onClick={() => handleStatusChange(el.id, ElectionStatus.CANCELLED)}
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

      <CreateElection
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={handleCreated}
      />
      <EditElection
        open={editElection !== null}
        election={editElection}
        onClose={() => setEditElection(null)}
        onUpdated={() => { setEditElection(null); loadData(); }}
      />
      <ReopenWindowModal
        open={reopenTarget !== null}
        kind="election"
        title={reopenTarget?.title ?? ""}
        currentVotingOpens={reopenTarget?.voting_opens}
        currentVotingCloses={reopenTarget?.voting_closes}
        onClose={() => setReopenTarget(null)}
        onConfirm={handleReopenConfirm}
      />
    </div>
  );
};

export default ManageElectionsPage;
