import React, { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { useTheme } from "../../styles/ThemeContext";
import {
  getPageContentWrapperStyle,
  getPageTitleStyle,
  getSectionH2Style,
  getCardStyle,
  getCardTitleStyle,
  getCardTextStyle,
  getTabsContainerStyle,
  getTabButtonStyle,
  getTableStyle,
  getTableHeaderStyle,
  getTableCellStyle,
  getSelectStyle,
  getStatusBadgeStyle,
} from "../../styles/ui";
import VotesPerConstituencyChart from "../../features/admin/components/votesPerConstituencyChart";
import SeatAllocationChart from "../../features/admin/components/seatAllocationChart";
import ReportErrorModal from "../../features/admin/components/reportErrorModal";
import ManageOfficials from "../../features/admin/components/manageOfficials";
import { ElectionApiRepository } from "../../features/election/repositories/election-api.repository";
import { Election, ElectionStatus } from "../../features/election/model/election.model";

// --- Mock data (replace with backend when available) ---

/** Set to true to show Audit logs tab (admin only). */
const MOCK_USER_IS_ADMIN = true;

const electionApiRepository = new ElectionApiRepository();

function datePartFromIso(iso: string | undefined): string | undefined {
  if (!iso) return undefined;
  return iso.includes("T") ? iso.split("T")[0] : iso.slice(0, 10);
}

/** Sort: open elections first, then by title. */
function sortElectionsForSelect(rows: Election[]): Election[] {
  return [...rows].sort((a, b) => {
    const rank = (e: Election) => (e.status === ElectionStatus.OPEN ? 0 : 1);
    const byStatus = rank(a) - rank(b);
    if (byStatus !== 0) return byStatus;
    return a.title.localeCompare(b.title, undefined, { sensitivity: "base" });
  });
}

function formatElectionOptionLabel(election: Election): string {
  const open = election.status === ElectionStatus.OPEN;
  const statusWord = open ? "Open" : "Closed";
  if (open) {
    const opens = datePartFromIso(election.voting_opens);
    return opens ? `${election.title} (${statusWord} · opens ${opens})` : `${election.title} (${statusWord})`;
  }
  const closes = datePartFromIso(election.voting_closes);
  return closes ? `${election.title} (${statusWord} · closed ${closes})` : `${election.title} (${statusWord})`;
}

interface ConstituencyResult {
  id: string;
  name: string;
  votesCast: number;
  votersWhoVoted: number;
  matchStatus: "ok" | "mismatch" | "pending";
}

interface SeatAllocation {
  party: string;
  seats: number;
  fill: string;
}

interface AuditLogEntry {
  id: string;
  timestamp: string;
  action: string;
  userId: string;
  details: string;
}

interface Investigation {
  id: string;
  title: string;
  status: "open" | "in_progress" | "resolved";
  reportedAt: string;
}

const MOCK_CONSTITUENCY_RESULTS: ConstituencyResult[] = [
  { id: "c1", name: "Edinburgh North", votesCast: 45231, votersWhoVoted: 45231, matchStatus: "ok" },
  { id: "c2", name: "Glasgow South", votesCast: 38102, votersWhoVoted: 38102, matchStatus: "ok" },
  { id: "c3", name: "Aberdeen Central", votesCast: 29450, votersWhoVoted: 29448, matchStatus: "mismatch" },
  { id: "c4", name: "Dundee West", votesCast: 22100, votersWhoVoted: 22100, matchStatus: "ok" },
  { id: "c5", name: "Inverness & Nairn", votesCast: 18500, votersWhoVoted: 18500, matchStatus: "ok" },
];

const MOCK_SEAT_ALLOCATIONS: SeatAllocation[] = [
  { party: "Party A", seats: 312, fill: "#1B2444" },
  { party: "Party B", seats: 242, fill: "#EF4444" },
  { party: "Party C", seats: 72, fill: "#F59E0B" },
  { party: "Party D", seats: 24, fill: "#22C55E" },
];

const MOCK_AUDIT_LOGS: AuditLogEntry[] = [
  { id: "a1", timestamp: "2024-07-06 09:15:00", action: "Verification started", userId: "official-001", details: "Election el-1 verification session started" },
  { id: "a2", timestamp: "2024-07-06 09:22:00", action: "Constituency checked", userId: "official-001", details: "Edinburgh North — vote count verified" },
  { id: "a3", timestamp: "2024-07-06 10:05:00", action: "Mismatch flagged", userId: "system", details: "Aberdeen Central — votesCast vs votersWhoVoted discrepancy" },
  { id: "a4", timestamp: "2024-07-06 10:30:00", action: "Error reported", userId: "official-002", details: "Report #ERR-1042 — ballot batch re-scan requested" },
  { id: "a5", timestamp: "2024-07-06 11:00:00", action: "Investigation created", userId: "official-001", details: "INV-008 — Aberdeen Central count investigation" },
];

const MOCK_INVESTIGATIONS: Investigation[] = [
  { id: "INV-008", title: "Aberdeen Central vote count discrepancy", status: "in_progress", reportedAt: "2024-07-06" },
  { id: "INV-007", title: "Duplicate ballot scan concern", status: "open", reportedAt: "2024-07-05" },
  { id: "INV-006", title: "Voter identity verification query", status: "resolved", reportedAt: "2024-07-04" },
  { id: "INV-005", title: "Biometric verification timeout", status: "resolved", reportedAt: "2024-07-03" },
];

const tabToSlug = (tab: string) => tab.replace(/\s+/g, "-");
const slugToTab = (slug: string) => slug.replace(/-/g, " ");

const OfficialHomePage: React.FC = () => {
  const { theme } = useTheme();
  const [searchParams, setSearchParams] = useSearchParams();
  const baseTabs = ["overview", "investigations"] as const;
  const tabs = MOCK_USER_IS_ADMIN ? (["overview", "audit logs", "investigations", "manage officials"] as const) : baseTabs;

  const tabFromUrl = searchParams.get("tab");
  const tabFromSlug = tabFromUrl ? slugToTab(tabFromUrl) : null;
  const resolvedTab: string =
    tabFromSlug && (tabs as readonly string[]).includes(tabFromSlug) ? tabFromSlug : tabs[0];

  const [activeTab, setActiveTab] = useState<string>(resolvedTab);
  const [selectedElectionId, setSelectedElectionId] = useState<string>("");
  const [elections, setElections] = useState<Election[]>([]);
  const [electionsLoadError, setElectionsLoadError] = useState<string | null>(null);
  const [electionsLoading, setElectionsLoading] = useState(true);
  const [reportErrorModalOpen, setReportErrorModalOpen] = useState(false);
  const [reportErrorContext, setReportErrorContext] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setElectionsLoading(true);
    setElectionsLoadError(null);
    electionApiRepository
      .listElections()
      .then((rows) => {
        if (cancelled) return;
        const sorted = sortElectionsForSelect(rows);
        setElections(sorted);
        if (sorted.length > 0) {
          setSelectedElectionId((current) =>
            current && sorted.some((e) => e.id === current) ? current : sorted[0].id,
          );
        } else {
          setSelectedElectionId("");
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setElectionsLoadError(err.message || "Failed to load elections.");
          setElections([]);
          setSelectedElectionId("");
        }
      })
      .finally(() => {
        if (!cancelled) setElectionsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("tab", tabToSlug(activeTab));
        return next;
      },
      { replace: true }
    );
  }, [activeTab, setSearchParams]);

  const selectedElection = elections.find((e) => e.id === selectedElectionId);
  const pageWrapper = getPageContentWrapperStyle(theme);
  const pageTitle = getPageTitleStyle(theme);
  const sectionH2 = getSectionH2Style(theme);
  const card = getCardStyle(theme);
  const cardTitle = getCardTitleStyle(theme);
  const cardText = getCardTextStyle(theme);

  const openReportError = (context?: string) => {
    setReportErrorContext(context ?? null);
    setReportErrorModalOpen(true);
  };

  return (
    <div style={{ ...pageWrapper }}>
      <h1 style={{ ...pageTitle }}>Election verification dashboard</h1>

      <section style={{ paddingLeft: theme.spacing.xl, paddingRight: theme.spacing.xl, paddingBottom: theme.spacing.lg }}>
        <label htmlFor="election-select" style={{ display: "block", marginBottom: theme.spacing.sm, color: theme.colors.text.secondary, fontSize: theme.fontSizes.sm }}>
          Select election to verify
        </label>
        <select
          id="election-select"
          value={selectedElectionId}
          onChange={(e) => setSelectedElectionId(e.target.value)}
          style={getSelectStyle(theme)}
          disabled={electionsLoading || !!electionsLoadError}
        >
          <option value="">
            {electionsLoading
              ? "Loading elections…"
              : electionsLoadError
                ? "— Error loading elections —"
                : elections.length === 0
                  ? "— No elections —"
                  : "— Select an election —"}
          </option>
          {elections.map((e) => (
            <option key={e.id} value={e.id}>
              {formatElectionOptionLabel(e)}
            </option>
          ))}
        </select>
        {electionsLoadError && (
          <p style={{ marginTop: theme.spacing.sm, color: theme.colors.status.error, fontSize: theme.fontSizes.sm }}>
            {electionsLoadError}
          </p>
        )}
      </section>

      {selectedElection && (
        <>
          <nav style={getTabsContainerStyle(theme)} aria-label="Dashboard sections">
            {tabs.map((tab) => (
              <button
                key={tab}
                type="button"
                style={getTabButtonStyle(theme, activeTab === tab)}
                onClick={() => setActiveTab(tab)}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>

          <div style={{ padding: theme.spacing.xl }}>
            {/* Overview: visualisations + constituency data + report error in context */}
            {activeTab === "overview" && (
              <section>
                <h2 style={sectionH2}>Overview</h2>
                <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
                  Summary and visualisations for <strong>{selectedElection.title}</strong>. Go through the constituency data below to verify results; use &quot;Report error&quot; when you see an issue.
                </p>

                {/* Charts row */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: theme.spacing.xl, marginBottom: theme.spacing.xl }}>
                  <VotesPerConstituencyChart data={MOCK_CONSTITUENCY_RESULTS} />
                  <SeatAllocationChart data={MOCK_SEAT_ALLOCATIONS} />
                </div>

                {/* Constituency data — go through the data; report error in context */}
                <div style={{ ...card, marginBottom: theme.spacing.lg }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: theme.spacing.sm, marginBottom: theme.spacing.md }}>
                    <h3 style={{ ...cardTitle, marginBottom: 0 }}>Constituency data</h3>
                    <button
                      type="button"
                      onClick={() => openReportError()}
                      style={{ ...getTabButtonStyle(theme, false), background: theme.colors.status.error, color: theme.colors.text.inverse }}
                    >
                      Report error
                    </button>
                  </div>
                  <p style={{ ...cardText, marginBottom: theme.spacing.md }}>
                    Verify vote count matches voters who voted. Report an error from here or from a specific row when you spot a discrepancy.
                  </p>
                  <div style={{ overflowX: "auto" }}>
                    <table style={getTableStyle(theme)}>
                      <thead>
                        <tr>
                          <th style={getTableHeaderStyle(theme)}>Constituency</th>
                          <th style={getTableHeaderStyle(theme)}>Votes cast</th>
                          <th style={getTableHeaderStyle(theme)}>Voters who voted</th>
                          <th style={getTableHeaderStyle(theme)}>Status</th>
                          <th style={getTableHeaderStyle(theme)}>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {MOCK_CONSTITUENCY_RESULTS.map((row) => (
                          <tr key={row.id}>
                            <td style={getTableCellStyle(theme)}>{row.name}</td>
                            <td style={getTableCellStyle(theme)}>{row.votesCast.toLocaleString()}</td>
                            <td style={getTableCellStyle(theme)}>{row.votersWhoVoted.toLocaleString()}</td>
                            <td style={getTableCellStyle(theme)}>
                              <span style={getStatusBadgeStyle(theme, row.matchStatus)}>{row.matchStatus}</span>
                            </td>
                            <td style={getTableCellStyle(theme)}>
                              <button
                                type="button"
                                onClick={() => openReportError(row.name)}
                                style={{ ...getTabButtonStyle(theme, false), padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}
                              >
                                Report error
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </section>
            )}

            {/* Audit logs — admin only */}
            {activeTab === "audit logs" && MOCK_USER_IS_ADMIN && (
              <section>
                <h2 style={sectionH2}>Audit logs</h2>
                <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
                  Chronological log of verification actions, system events, and official activity for this election. (Admin only.)
                </p>
                <div style={{ ...card, overflowX: "auto" }}>
                  <table style={getTableStyle(theme)}>
                    <thead>
                      <tr>
                        <th style={getTableHeaderStyle(theme)}>Timestamp</th>
                        <th style={getTableHeaderStyle(theme)}>Action</th>
                        <th style={getTableHeaderStyle(theme)}>User</th>
                        <th style={getTableHeaderStyle(theme)}>Details</th>
                      </tr>
                    </thead>
                    <tbody>
                      {MOCK_AUDIT_LOGS.map((entry) => (
                        <tr key={entry.id}>
                          <td style={getTableCellStyle(theme)}>{entry.timestamp}</td>
                          <td style={getTableCellStyle(theme)}>{entry.action}</td>
                          <td style={getTableCellStyle(theme)}>{entry.userId}</td>
                          <td style={getTableCellStyle(theme)}>{entry.details}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </section>
            )}

            {/* Investigations — all past and current */}
            {activeTab === "investigations" && (
              <section>
                <h2 style={sectionH2}>Investigations</h2>
                <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
                  All investigations for this election — past and current. Use this area to assist in investigations and track resolution status.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
                  {MOCK_INVESTIGATIONS.map((inv) => (
                    <div key={inv.id} style={card}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: theme.spacing.sm }}>
                        <div>
                          <h3 style={{ ...cardTitle, marginBottom: theme.spacing.xs }}>{inv.title}</h3>
                          <p style={{ ...cardText, marginBottom: 0, fontSize: theme.fontSizes.sm }}>
                            {inv.id} · Reported {inv.reportedAt}
                          </p>
                        </div>
                        <span style={getStatusBadgeStyle(theme, inv.status)}>{inv.status.replace("_", " ")}</span>
                      </div>
                      <p style={{ ...cardText, marginTop: theme.spacing.sm, marginBottom: 0, fontStyle: "italic" }}>
                        Investigation workflow and actions to be implemented.
                      </p>
                    </div>
                  ))}
                </div>
              </section>
            )}

            {/* Manage officials — admin only */}
            {activeTab === "manage officials" && MOCK_USER_IS_ADMIN && (
              <>
                <ManageOfficials />
              </>
            )}
          </div>
        </>
      )}

      {!selectedElection && (
        <p style={{ paddingLeft: theme.spacing.xl, color: theme.colors.text.secondary }}>
          Select an election above to view the verification dashboard and investigations.
        </p>
      )}

      <ReportErrorModal
        open={reportErrorModalOpen}
        onClose={() => setReportErrorModalOpen(false)}
        context={reportErrorContext}
      />
    </div>
  );
};

export default OfficialHomePage;
