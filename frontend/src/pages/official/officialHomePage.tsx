import React, { useState, useEffect, useCallback } from "react";
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
import type { StatusBadgeVariant } from "../../styles/ui";
import VotesPerConstituencyChart from "../../features/officials/components/votesPerConstituencyChart";
import SeatAllocationChart from "../../features/officials/components/seatAllocationChart";
import ReportErrorModal from "../../features/officials/components/reportErrorModal";
import { ElectionApiRepository } from "../../features/election/repositories/election-api.repository";
import { ReferendumApiRepository } from "../../features/referendum/repositories/referendum-api.repository";
import { ResultApiRepository } from "../../features/results/repositories/result-api.repository";
import { OfficialApiRepository } from "../../features/officials/repositories/official-api.repository";
import { AuditLogApiRepository } from "../../features/officials/repositories/audit-log-api.repository";
import { ConstituencyApiRepository } from "../../features/election/repositories/constituency-api.repository";
import { PartyApiRepository } from "../../features/election/repositories/candidate-api.repository";
import { InvestigationApiRepository } from "../../features/investigation/repositories/investigation-api.repository";
import { Election, ElectionStatus, ELECTION_TYPE_LABELS, ALLOCATION_METHOD_LABELS } from "../../features/election/model/election.model";
import { Referendum, ReferendumStatus } from "../../features/referendum/model/referendum.model";
import { ElectionResult, ReferendumResult } from "../../features/results/model/result.model";
import { Constituency } from "../../features/election/model/constituency.model";
import { Party } from "../../features/election/model/candidate.model";
import { OfficialRole } from "../../features/officials/model/official.model";
import type { ElectionAuditReport, ReferendumAuditReport } from "../../features/officials/model/audit-report.model";
import { generateElectionAuditPdf, generateReferendumAuditPdf } from "../../features/officials/components/auditReportGenerator";
import { Investigation } from "../../features/investigation/models/investigation.model";
import { Official } from "../../features/officials/model/official.model";
import UpdateInvestigationModal from "../../features/investigation/components/updateInvestigationModal";
import { getAccessTokenSubject } from "../../services/api-client.service";

const electionApiRepository = new ElectionApiRepository();
const referendumApiRepository = new ReferendumApiRepository();
const resultApiRepository = new ResultApiRepository();
const officialApiRepository = new OfficialApiRepository();
const auditLogApiRepository = new AuditLogApiRepository();
const constituencyApiRepository = new ConstituencyApiRepository();
const partyApiRepository = new PartyApiRepository();
const investigationApiRepository = new InvestigationApiRepository();

// ── Helpers ──

function datePartFromIso(iso: string | undefined): string | undefined {
  if (!iso) return undefined;
  return iso.includes("T") ? iso.split("T")[0] : iso.slice(0, 10);
}

function formatDateTime(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
}

type SelectableItem = { id: string; title: string; status: string; kind: "election" | "referendum"; voting_opens?: string; voting_closes?: string };

/** Derive the effective status from the voting schedule if the backend status is stale. */
function effectiveStatus(backendStatus: string, votingOpens?: string, votingCloses?: string): string {
  if (backendStatus === "CANCELLED" || backendStatus === "DRAFT") return backendStatus;
  const now = Date.now();
  if (votingCloses) {
    const close = Date.parse(votingCloses);
    if (!isNaN(close) && now > close) return "CLOSED";
  }
  if (votingOpens) {
    const open = Date.parse(votingOpens);
    if (!isNaN(open) && now < open) return "CLOSED";
  }
  return backendStatus;
}

function sortItemsForSelect(items: SelectableItem[]): SelectableItem[] {
  return [...items].sort((a, b) => {
    const rank = (e: SelectableItem) => (e.status === "OPEN" ? 0 : e.status === "CLOSED" ? 1 : 2);
    const byStatus = rank(a) - rank(b);
    if (byStatus !== 0) return byStatus;
    return a.title.localeCompare(b.title, undefined, { sensitivity: "base" });
  });
}

function formatOptionLabel(item: SelectableItem): string {
  const typeLabel = item.kind === "referendum" ? "Referendum" : "Election";
  const statusWord = item.status === "CANCELLED" ? "Cancelled" : item.status === "OPEN" ? "Open" : "Closed";
  const dateStr = item.status === "OPEN"
    ? (datePartFromIso(item.voting_opens) ? ` · opens ${datePartFromIso(item.voting_opens)}` : "")
    : (datePartFromIso(item.voting_closes) ? ` · closed ${datePartFromIso(item.voting_closes)}` : "");
  return `[${typeLabel}] ${item.title} (${statusWord}${dateStr})`;
}


const tabToSlug = (tab: string) => tab.replace(/\s+/g, "-");
const slugToTab = (slug: string) => slug.replace(/-/g, " ");

const OfficialHomePage: React.FC = () => {
  const { theme } = useTheme();
  const [searchParams, setSearchParams] = useSearchParams();

  // ── Current official and admin check ──
  const [isAdmin, setIsAdmin] = useState(false);
  const [adminLoading, setAdminLoading] = useState(true);

  useEffect(() => {
    const officialId = getAccessTokenSubject();
    if (!officialId) { setAdminLoading(false); return; }
    officialApiRepository.getOfficial(officialId)
      .then((official) => setIsAdmin(official.role === OfficialRole.ADMIN))
      .catch(() => setIsAdmin(false))
      .finally(() => setAdminLoading(false));
  }, []);

  const baseTabs = ["overview", "investigations"] as const;
  const tabs = isAdmin
    ? (["overview", "audit logs", "investigations"] as const)
    : baseTabs;

  const tabFromUrl = searchParams.get("tab");
  const tabFromSlug = tabFromUrl ? slugToTab(tabFromUrl) : null;
  const resolvedTab: string =
    tabFromSlug && (tabs as readonly string[]).includes(tabFromSlug) ? tabFromSlug : tabs[0];

  const [activeTab, setActiveTab] = useState<string>(resolvedTab);

  // ── Elections + referendums selector ──
  const [selectableItems, setSelectableItems] = useState<SelectableItem[]>([]);
  const [selectedItemId, setSelectedItemId] = useState<string>("");
  const [itemsLoading, setItemsLoading] = useState(true);
  const [itemsLoadError, setItemsLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    setItemsLoading(true);
    setItemsLoadError(null);

    Promise.all([
      electionApiRepository.listElections(),
      referendumApiRepository.listReferendums(),
    ])
      .then(([elections, referendums]) => {
        if (cancelled) return;
        const electionItems: SelectableItem[] = elections.map((e) => ({
          id: e.id, title: e.title,
          status: effectiveStatus(e.status, e.voting_opens, e.voting_closes),
          kind: "election" as const,
          voting_opens: e.voting_opens, voting_closes: e.voting_closes,
        }));
        const referendumItems: SelectableItem[] = referendums.map((r) => ({
          id: r.id, title: r.title,
          status: effectiveStatus(r.status, r.voting_opens, r.voting_closes),
          kind: "referendum" as const,
          voting_opens: r.voting_opens, voting_closes: r.voting_closes,
        }));
        const sorted = sortItemsForSelect([...electionItems, ...referendumItems]);
        setSelectableItems(sorted);
        if (sorted.length > 0) {
          setSelectedItemId((current) =>
            current && sorted.some((i) => i.id === current) ? current : sorted[0].id,
          );
        } else {
          setSelectedItemId("");
        }
      })
      .catch((err: Error) => {
        if (!cancelled) {
          setItemsLoadError(err.message || "Failed to load elections and referendums.");
          setSelectableItems([]);
          setSelectedItemId("");
        }
      })
      .finally(() => { if (!cancelled) setItemsLoading(false); });

    return () => { cancelled = true; };
  }, []);

  const selectedItem = selectableItems.find((i) => i.id === selectedItemId);

  // ── Results data ──
  const [electionResult, setElectionResult] = useState<ElectionResult | null>(null);
  const [referendumResult, setReferendumResult] = useState<ReferendumResult | null>(null);
  const [resultsLoading, setResultsLoading] = useState(false);
  const [resultsError, setResultsError] = useState<string | null>(null);

  // ── Lookup maps ──
  const [constituencyMap, setConstituencyMap] = useState<Record<string, Constituency>>({});
  const [partyMap, setPartyMap] = useState<Record<string, Party>>({});

  useEffect(() => {
    constituencyApiRepository.listConstituencies()
      .then((rows) => {
        const map: Record<string, Constituency> = {};
        for (const c of rows) map[c.id] = c;
        setConstituencyMap(map);
      })
      .catch(() => {});
    partyApiRepository.listParties()
      .then((rows) => {
        const map: Record<string, Party> = {};
        for (const p of rows) map[p.id] = p;
        setPartyMap(map);
      })
      .catch(() => {});
  }, []);

  const votingClosed = selectedItem
    ? selectedItem.status === "CLOSED" ||
      (selectedItem.voting_closes != null && selectedItem.voting_closes !== "" && Date.now() > Date.parse(selectedItem.voting_closes))
    : false;

  const loadResults = useCallback(() => {
    if (!selectedItem) return;
    setElectionResult(null);
    setReferendumResult(null);
    setResultsError(null);

    if (!votingClosed) {
      setResultsLoading(false);
      return;
    }

    setResultsLoading(true);

    if (selectedItem.kind === "election") {
      resultApiRepository.getElectionResults(selectedItem.id)
        .then(setElectionResult)
        .catch((err: Error) => setResultsError(err.message || "Failed to load results."))
        .finally(() => setResultsLoading(false));
    } else {
      resultApiRepository.getReferendumResults(selectedItem.id)
        .then(setReferendumResult)
        .catch((err: Error) => setResultsError(err.message || "Failed to load results."))
        .finally(() => setResultsLoading(false));
    }
  }, [selectedItem, votingClosed]);

  useEffect(() => { loadResults(); }, [loadResults]);

  // ── Audit report ──
  const [auditReportLoading, setAuditReportLoading] = useState(false);
  const [auditReportError, setAuditReportError] = useState<string | null>(null);

  const handleDownloadAuditReport = useCallback(() => {
    if (!selectedItem || !isAdmin) return;
    setAuditReportLoading(true);
    setAuditReportError(null);

    if (selectedItem.kind === "election") {
      auditLogApiRepository.getElectionAuditReport(selectedItem.id)
        .then((report: ElectionAuditReport) => generateElectionAuditPdf(report, partyMap))
        .catch((err: Error) => setAuditReportError(err.message || "Failed to generate audit report."))
        .finally(() => setAuditReportLoading(false));
    } else {
      auditLogApiRepository.getReferendumAuditReport(selectedItem.id)
        .then((report: ReferendumAuditReport) => generateReferendumAuditPdf(report))
        .catch((err: Error) => setAuditReportError(err.message || "Failed to generate audit report."))
        .finally(() => setAuditReportLoading(false));
    }
  }, [selectedItem, isAdmin, partyMap]);

  // ── Investigations ──
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [investigationsLoading, setInvestigationsLoading] = useState(false);
  const [investigationsError, setInvestigationsError] = useState<string | null>(null);

  const loadInvestigations = useCallback(() => {
    if (!selectedItem || selectedItem.kind !== "election") {
      setInvestigations([]);
      return;
    }
    setInvestigationsLoading(true);
    setInvestigationsError(null);
    investigationApiRepository.getInvestigationsByElection(selectedItem.id)
      .then(setInvestigations)
      .catch((err: Error) => { setInvestigationsError(err.message || "Failed to load investigations."); setInvestigations([]); })
      .finally(() => setInvestigationsLoading(false));
  }, [selectedItem]);

  useEffect(() => { loadInvestigations(); }, [loadInvestigations]);

  // ── Constituency table pagination ──
  const CONSTITUENCIES_PER_PAGE = 20;
  const [constituencyPage, setConstituencyPage] = useState(0);

  // Reset to first page when a different election is selected
  useEffect(() => { setConstituencyPage(0); }, [selectedItemId]);

  // ── Officials list (for investigation assignment) ──
  const [officialsList, setOfficialsList] = useState<Official[]>([]);
  useEffect(() => {
    officialApiRepository.listOfficials()
      .then(setOfficialsList)
      .catch(() => setOfficialsList([]));
  }, []);

  // ── Update investigation modal ──
  const [updateInvModalOpen, setUpdateInvModalOpen] = useState(false);
  const [selectedInvestigation, setSelectedInvestigation] = useState<Investigation | null>(null);

  const openUpdateInvestigation = (inv: Investigation) => {
    setSelectedInvestigation(inv);
    setUpdateInvModalOpen(true);
  };

  // ── Report error modal ──
  const [reportErrorModalOpen, setReportErrorModalOpen] = useState(false);
  const [reportErrorContext, setReportErrorContext] = useState<string | null>(null);

  const openReportError = (context?: string) => {
    setReportErrorContext(context ?? null);
    setReportErrorModalOpen(true);
  };

  const handleReportSubmitted = () => {
    setReportErrorModalOpen(false);
    loadInvestigations();
  };

  // ── Tab URL sync ──
  useEffect(() => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.set("tab", tabToSlug(activeTab));
        return next;
      },
      { replace: true },
    );
  }, [activeTab, setSearchParams]);

  // ── Derived data for charts ──
  const MAX_CHART_CONSTITUENCIES = 20;
  const allConstituencyChartData = (electionResult?.constituencies ?? []).map((c) => ({
    id: c.constituency_id,
    name: constituencyMap[c.constituency_id]?.name ?? c.constituency_id.slice(0, 8),
    votesCast: c.total_votes,
  }));
  const constituencyChartData = allConstituencyChartData.length > MAX_CHART_CONSTITUENCIES
    ? [...allConstituencyChartData].sort((a, b) => b.votesCast - a.votesCast).slice(0, MAX_CHART_CONSTITUENCIES)
    : allConstituencyChartData;
  const chartTruncated = allConstituencyChartData.length > MAX_CHART_CONSTITUENCIES;

  const seatAllocationData = Object.entries(electionResult?.seat_allocation ?? {}).map(([partyId, seats], i) => ({
    party: partyMap[partyId]?.party_name ?? partyMap[partyId]?.abbreviation ?? partyId.slice(0, 8),
    seats,
    fill: theme.colors.chart[i % theme.colors.chart.length],
  }));

  // ── Paginated constituency list ──
  const allConstituencies = electionResult?.constituencies ?? [];
  const totalConstituencyPages = Math.max(1, Math.ceil(allConstituencies.length / CONSTITUENCIES_PER_PAGE));
  const paginatedConstituencies = allConstituencies.slice(
    constituencyPage * CONSTITUENCIES_PER_PAGE,
    (constituencyPage + 1) * CONSTITUENCIES_PER_PAGE,
  );

  // ── Styles ──
  const pageWrapper = getPageContentWrapperStyle(theme);
  const pageTitle = getPageTitleStyle(theme);
  const sectionH2 = getSectionH2Style(theme);
  const card = getCardStyle(theme);
  const cardTitle = getCardTitleStyle(theme);
  const cardText = getCardTextStyle(theme);

  const summaryCardStyle: React.CSSProperties = {
    ...card,
    textAlign: "center",
    padding: theme.spacing.lg,
  };

  const summaryValueStyle: React.CSSProperties = {
    fontSize: theme.fontSizes["2xl"],
    fontWeight: theme.fontWeights.bold,
    color: theme.colors.text.primary,
    margin: 0,
  };

  const summaryLabelStyle: React.CSSProperties = {
    fontSize: theme.fontSizes.sm,
    color: theme.colors.text.secondary,
    margin: `${theme.spacing.xs} 0 0 0`,
  };

  const investStatusToBadge = (s: string): StatusBadgeVariant => {
    const lower = s.toLowerCase();
    if (lower === "resolved" || lower === "closed") return "resolved";
    if (lower === "in_progress") return "in_progress";
    return "open";
  };

  if (adminLoading) {
    return (
      <div style={pageWrapper}>
        <h1 style={pageTitle}>Vote Verification Dashboard</h1>
        <p style={{ paddingLeft: theme.spacing.xl, color: theme.colors.text.secondary }}>Loading…</p>
      </div>
    );
  }

  return (
    <div style={pageWrapper}>
      <h1 style={pageTitle}>Vote Verification Dashboard</h1>

      {/* Election / Referendum selector */}
      <section style={{ paddingLeft: theme.spacing.xl, paddingRight: theme.spacing.xl, paddingBottom: theme.spacing.lg }}>
        <label
          htmlFor="election-select"
          style={{ display: "block", marginBottom: theme.spacing.sm, color: theme.colors.text.secondary, fontSize: theme.fontSizes.sm }}
        >
          Select election or referendum to verify
        </label>
        <select
          id="election-select"
          value={selectedItemId}
          onChange={(e) => setSelectedItemId(e.target.value)}
          style={getSelectStyle(theme)}
          disabled={itemsLoading || !!itemsLoadError}
        >
          <option value="">
            {itemsLoading
              ? "Loading…"
              : itemsLoadError
                ? "— Error loading —"
                : selectableItems.length === 0
                  ? "— No elections or referendums —"
                  : "— Select —"}
          </option>
          {selectableItems.map((item) => (
            <option key={item.id} value={item.id}>
              {formatOptionLabel(item)}
            </option>
          ))}
        </select>
        {itemsLoadError && (
          <p style={{ marginTop: theme.spacing.sm, color: theme.colors.status.error, fontSize: theme.fontSizes.sm }}>
            {itemsLoadError}
          </p>
        )}
      </section>

      {selectedItem && (
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

            {/* ─── OVERVIEW TAB ─── */}
            {activeTab === "overview" && (
              <section>
                <h2 style={sectionH2}>Overview — {selectedItem.title}</h2>

                {resultsLoading && (
                  <p style={{ ...cardText, color: theme.colors.text.secondary }}>Loading results…</p>
                )}

                {resultsError && (
                  <div style={{ ...card, borderLeft: `4px solid ${theme.colors.status.error}`, marginBottom: theme.spacing.lg }}>
                    <p style={{ ...cardText, margin: 0, color: theme.colors.status.error }}>
                      {resultsError}
                    </p>
                    <button
                      type="button"
                      onClick={loadResults}
                      style={{ ...getTabButtonStyle(theme, false), marginTop: theme.spacing.sm, fontSize: theme.fontSizes.sm }}
                    >
                      Retry
                    </button>
                  </div>
                )}

                {/* ── Election results overview ── */}
                {!resultsLoading && !resultsError && electionResult && selectedItem.kind === "election" && (
                  <>
                    {/* Summary cards row */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: theme.spacing.lg, marginBottom: theme.spacing.xl }}>
                      <div style={summaryCardStyle}>
                        <p style={summaryValueStyle}>{electionResult.total_votes.toLocaleString()}</p>
                        <p style={summaryLabelStyle}>Total votes cast</p>
                      </div>
                      <div style={summaryCardStyle}>
                        <p style={summaryValueStyle}>{electionResult.total_seats}</p>
                        <p style={summaryLabelStyle}>Total seats</p>
                      </div>
                      <div style={summaryCardStyle}>
                        <p style={summaryValueStyle}>{electionResult.majority_threshold}</p>
                        <p style={summaryLabelStyle}>Majority threshold</p>
                      </div>
                      <div style={summaryCardStyle}>
                        <p style={summaryValueStyle}>{electionResult.constituencies.length}</p>
                        <p style={summaryLabelStyle}>Constituencies reporting</p>
                      </div>
                      <div style={summaryCardStyle}>
                        <p style={{
                          ...summaryValueStyle,
                          color: electionResult.winning_party_id ? theme.colors.status.success : theme.colors.text.secondary,
                        }}>
                          {electionResult.winning_party_id
                            ? (partyMap[electionResult.winning_party_id]?.party_name ?? electionResult.winning_party_id.slice(0, 8))
                            : "No majority"}
                        </p>
                        <p style={summaryLabelStyle}>Winning party</p>
                      </div>
                      <div style={summaryCardStyle}>
                        <p style={summaryValueStyle}>
                          <span style={getStatusBadgeStyle(theme, electionResult.status === "CLOSED" ? "resolved" : electionResult.status === "OPEN" ? "open" : "mismatch")}>
                            {electionResult.status}
                          </span>
                        </p>
                        <p style={summaryLabelStyle}>Election status</p>
                      </div>
                    </div>

                    {/* Charts row */}
                    {constituencyChartData.length > 0 && (
                      <div style={{ display: "grid", gridTemplateColumns: seatAllocationData.length > 0 ? "1fr 1fr" : "1fr", gap: theme.spacing.xl, marginBottom: theme.spacing.xl }}>
                        <VotesPerConstituencyChart
                          data={constituencyChartData}
                          title={chartTruncated ? `Top ${MAX_CHART_CONSTITUENCIES} constituencies by votes` : "Votes per constituency"}
                        />
                        {seatAllocationData.length > 0 && (
                          <SeatAllocationChart data={seatAllocationData} />
                        )}
                      </div>
                    )}

                    {/* Seat allocation detail table */}
                    {seatAllocationData.length > 0 && (
                      <div style={{ ...card, marginBottom: theme.spacing.lg }}>
                        <h3 style={{ ...cardTitle, marginBottom: theme.spacing.md }}>Seat allocation by party</h3>
                        <div style={{ overflowX: "auto" }}>
                          <table style={getTableStyle(theme)}>
                            <thead>
                              <tr>
                                <th style={getTableHeaderStyle(theme)}>Party</th>
                                <th style={getTableHeaderStyle(theme)}>Seats won</th>
                                <th style={getTableHeaderStyle(theme)}>% of seats</th>
                              </tr>
                            </thead>
                            <tbody>
                              {seatAllocationData.map((row) => (
                                <tr key={row.party}>
                                  <td style={getTableCellStyle(theme)}>
                                    <span style={{ display: "inline-block", width: 12, height: 12, borderRadius: "50%", background: row.fill, marginRight: theme.spacing.sm, verticalAlign: "middle" }} />
                                    {row.party}
                                  </td>
                                  <td style={getTableCellStyle(theme)}>{row.seats}</td>
                                  <td style={getTableCellStyle(theme)}>
                                    {electionResult.total_seats > 0 ? ((row.seats / electionResult.total_seats) * 100).toFixed(1) + "%" : "—"}
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}

                    {/* Constituency results table (paginated) */}
                    <div style={{ ...card, marginBottom: theme.spacing.lg }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: theme.spacing.sm, marginBottom: theme.spacing.md }}>
                        <h3 style={{ ...cardTitle, marginBottom: 0 }}>
                          Constituency results
                          {allConstituencies.length > CONSTITUENCIES_PER_PAGE && (
                            <span style={{ fontSize: theme.fontSizes.sm, fontWeight: theme.fontWeights.normal, color: theme.colors.text.secondary, marginLeft: theme.spacing.sm }}>
                              ({constituencyPage * CONSTITUENCIES_PER_PAGE + 1}–{Math.min((constituencyPage + 1) * CONSTITUENCIES_PER_PAGE, allConstituencies.length)} of {allConstituencies.length})
                            </span>
                          )}
                        </h3>
                        <button
                          type="button"
                          onClick={() => openReportError()}
                          style={{ ...getTabButtonStyle(theme, false), background: theme.colors.status.error, color: theme.colors.text.inverse }}
                        >
                          Report error
                        </button>
                      </div>
                      {allConstituencies.length === 0 ? (
                        <p style={{ ...cardText, fontStyle: "italic" }}>No constituency results available yet.</p>
                      ) : (
                        <>
                          <div style={{ overflowX: "auto" }}>
                            <table style={getTableStyle(theme)}>
                              <thead>
                                <tr>
                                  <th style={getTableHeaderStyle(theme)}>Constituency</th>
                                  <th style={getTableHeaderStyle(theme)}>Winner</th>
                                  <th style={getTableHeaderStyle(theme)}>Winning party</th>
                                  <th style={getTableHeaderStyle(theme)}>Total votes</th>
                                  <th style={getTableHeaderStyle(theme)}>Candidates</th>
                                  <th style={getTableHeaderStyle(theme)}>Actions</th>
                                </tr>
                              </thead>
                              <tbody>
                                {paginatedConstituencies.map((c) => {
                                  const cName = constituencyMap[c.constituency_id]?.name ?? c.constituency_id.slice(0, 8);
                                  const winnerPartyName = c.winner_party_id
                                    ? (partyMap[c.winner_party_id]?.party_name ?? c.winner_party_id.slice(0, 8))
                                    : "—";
                                  return (
                                    <tr key={c.constituency_id}>
                                      <td style={getTableCellStyle(theme)}>{cName}</td>
                                      <td style={getTableCellStyle(theme)}>{c.winner_name || "—"}</td>
                                      <td style={getTableCellStyle(theme)}>{winnerPartyName}</td>
                                      <td style={getTableCellStyle(theme)}>{c.total_votes.toLocaleString()}</td>
                                      <td style={getTableCellStyle(theme)}>{c.tallies.length}</td>
                                      <td style={getTableCellStyle(theme)}>
                                        <button
                                          type="button"
                                          onClick={() => openReportError(cName)}
                                          style={{ ...getTabButtonStyle(theme, false), padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}
                                        >
                                          Report error
                                        </button>
                                      </td>
                                    </tr>
                                  );
                                })}
                              </tbody>
                            </table>
                          </div>
                          {totalConstituencyPages > 1 && (
                            <div style={{ display: "flex", justifyContent: "center", alignItems: "center", gap: theme.spacing.md, marginTop: theme.spacing.md }}>
                              <button
                                type="button"
                                disabled={constituencyPage === 0}
                                onClick={() => setConstituencyPage((p) => Math.max(0, p - 1))}
                                style={{ ...getTabButtonStyle(theme, false), opacity: constituencyPage === 0 ? 0.4 : 1 }}
                              >
                                Previous
                              </button>
                              <span style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary }}>
                                Page {constituencyPage + 1} of {totalConstituencyPages}
                              </span>
                              <button
                                type="button"
                                disabled={constituencyPage >= totalConstituencyPages - 1}
                                onClick={() => setConstituencyPage((p) => Math.min(totalConstituencyPages - 1, p + 1))}
                                style={{ ...getTabButtonStyle(theme, false), opacity: constituencyPage >= totalConstituencyPages - 1 ? 0.4 : 1 }}
                              >
                                Next
                              </button>
                            </div>
                          )}
                        </>
                      )}
                    </div>
                  </>
                )}

                {/* ── Referendum results overview ── */}
                {!resultsLoading && !resultsError && referendumResult && selectedItem.kind === "referendum" && (
                  <>
                    {/* Summary cards */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))", gap: theme.spacing.lg, marginBottom: theme.spacing.xl }}>
                      <div style={summaryCardStyle}>
                        <p style={summaryValueStyle}>{referendumResult.total_votes.toLocaleString()}</p>
                        <p style={summaryLabelStyle}>Total votes cast</p>
                      </div>
                      <div style={summaryCardStyle}>
                        <p style={{ ...summaryValueStyle, color: theme.colors.status.success }}>{referendumResult.yes_votes.toLocaleString()}</p>
                        <p style={summaryLabelStyle}>Yes votes</p>
                      </div>
                      <div style={summaryCardStyle}>
                        <p style={{ ...summaryValueStyle, color: theme.colors.status.error }}>{referendumResult.no_votes.toLocaleString()}</p>
                        <p style={summaryLabelStyle}>No votes</p>
                      </div>
                      <div style={summaryCardStyle}>
                        <p style={{
                          ...summaryValueStyle,
                          color: referendumResult.outcome === "YES" ? theme.colors.status.success
                            : referendumResult.outcome === "NO" ? theme.colors.status.error
                            : theme.colors.text.secondary,
                        }}>
                          {referendumResult.outcome || "Pending"}
                        </p>
                        <p style={summaryLabelStyle}>Outcome</p>
                      </div>
                      {referendumResult.total_votes > 0 && (
                        <>
                          <div style={summaryCardStyle}>
                            <p style={summaryValueStyle}>
                              {((referendumResult.yes_votes / referendumResult.total_votes) * 100).toFixed(1)}%
                            </p>
                            <p style={summaryLabelStyle}>Yes percentage</p>
                          </div>
                          <div style={summaryCardStyle}>
                            <p style={summaryValueStyle}>
                              {((referendumResult.no_votes / referendumResult.total_votes) * 100).toFixed(1)}%
                            </p>
                            <p style={summaryLabelStyle}>No percentage</p>
                          </div>
                        </>
                      )}
                    </div>

                    {/* Referendum bar chart */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr", gap: theme.spacing.xl, marginBottom: theme.spacing.xl }}>
                      <SeatAllocationChart
                        data={[
                          { party: "Yes", seats: referendumResult.yes_votes, fill: theme.colors.status.success },
                          { party: "No", seats: referendumResult.no_votes, fill: theme.colors.status.error },
                        ]}
                        title="Vote breakdown"
                      />
                    </div>

                    <div style={{ ...card, marginBottom: theme.spacing.lg }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: theme.spacing.sm }}>
                        <h3 style={{ ...cardTitle, marginBottom: 0 }}>Referendum summary</h3>
                        <button
                          type="button"
                          onClick={() => openReportError()}
                          style={{ ...getTabButtonStyle(theme, false), background: theme.colors.status.error, color: theme.colors.text.inverse }}
                        >
                          Report error
                        </button>
                      </div>
                      <div style={{ overflowX: "auto", marginTop: theme.spacing.md }}>
                        <table style={getTableStyle(theme)}>
                          <thead>
                            <tr>
                              <th style={getTableHeaderStyle(theme)}>Metric</th>
                              <th style={getTableHeaderStyle(theme)}>Value</th>
                            </tr>
                          </thead>
                          <tbody>
                            <tr>
                              <td style={getTableCellStyle(theme)}>Total votes</td>
                              <td style={getTableCellStyle(theme)}>{referendumResult.total_votes.toLocaleString()}</td>
                            </tr>
                            <tr>
                              <td style={getTableCellStyle(theme)}>Yes votes</td>
                              <td style={getTableCellStyle(theme)}>{referendumResult.yes_votes.toLocaleString()}</td>
                            </tr>
                            <tr>
                              <td style={getTableCellStyle(theme)}>No votes</td>
                              <td style={getTableCellStyle(theme)}>{referendumResult.no_votes.toLocaleString()}</td>
                            </tr>
                            <tr>
                              <td style={getTableCellStyle(theme)}>Outcome</td>
                              <td style={getTableCellStyle(theme)}>
                                <span style={getStatusBadgeStyle(theme, referendumResult.outcome === "YES" ? "ok" : referendumResult.outcome === "NO" ? "mismatch" : "pending")}>
                                  {referendumResult.outcome || "Pending"}
                                </span>
                              </td>
                            </tr>
                          </tbody>
                        </table>
                      </div>
                    </div>
                  </>
                )}

                {/* Voting not yet closed */}
                {!resultsLoading && !resultsError && !votingClosed && (
                  <div style={{ ...card, textAlign: "center", padding: theme.spacing.xl, borderLeft: `4px solid ${theme.colors.status.warning}` }}>
                    <p style={{ ...cardText, margin: 0, fontWeight: theme.fontWeights.medium }}>
                      Voting has not yet closed for this {selectedItem.kind}.
                    </p>
                    <p style={{ ...cardText, margin: `${theme.spacing.sm} 0 0 0`, color: theme.colors.text.secondary }}>
                      Results will become available to officials once the voting period ends and the status changes to Closed.
                    </p>
                  </div>
                )}

                {/* Voting closed but no results data */}
                {!resultsLoading && !resultsError && votingClosed && !electionResult && !referendumResult && (
                  <div style={{ ...card, textAlign: "center", padding: theme.spacing.xl }}>
                    <p style={{ ...cardText, margin: 0, color: theme.colors.text.secondary }}>
                      No results available yet for this {selectedItem.kind}. Tallying may still be in progress.
                    </p>
                  </div>
                )}
              </section>
            )}

            {/* ─── AUDIT REPORT TAB (admin only) ─── */}
            {activeTab === "audit logs" && isAdmin && (
              <section>
                <h2 style={sectionH2}>Audit report</h2>
                <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
                  Generate a formal audit report for this {selectedItem.kind}. The report contains aggregate
                  statistics, system event timelines, official activity, and investigation summaries.
                  It does not contain any voter-identifiable information. (Admin only.)
                </p>

                <div style={{ ...card, textAlign: "center", padding: theme.spacing.xl }}>
                  <p style={{ ...cardText, marginBottom: theme.spacing.lg, color: theme.colors.text.secondary }}>
                    The audit report is a PDF document suitable for legal and compliance purposes.
                    It includes election metadata, turnout figures, result summaries, system integrity events,
                    and investigation records — with no individual voter data.
                  </p>

                  <button
                    type="button"
                    onClick={handleDownloadAuditReport}
                    disabled={auditReportLoading}
                    style={{
                      ...getTabButtonStyle(theme, true),
                      padding: `${theme.spacing.md} ${theme.spacing.xl}`,
                      fontSize: theme.fontSizes.base,
                      opacity: auditReportLoading ? 0.6 : 1,
                    }}
                  >
                    {auditReportLoading ? "Generating report…" : "Download audit report (PDF)"}
                  </button>

                  {auditReportError && (
                    <div style={{ ...card, borderLeft: `4px solid ${theme.colors.status.error}`, marginTop: theme.spacing.lg, textAlign: "left" }}>
                      <p style={{ ...cardText, margin: 0, color: theme.colors.status.error }}>
                        {auditReportError}
                      </p>
                    </div>
                  )}
                </div>
              </section>
            )}

            {/* ─── INVESTIGATIONS TAB ─── */}
            {activeTab === "investigations" && (
              <section>
                <h2 style={sectionH2}>Investigations</h2>
                <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
                  All investigations for this {selectedItem.kind} — past and current.
                </p>

                {selectedItem.kind === "referendum" && (
                  <p style={{ ...cardText, fontStyle: "italic", color: theme.colors.text.secondary }}>
                    Investigations are available for elections only.
                  </p>
                )}

                {selectedItem.kind === "election" && investigationsLoading && (
                  <p style={{ ...cardText, color: theme.colors.text.secondary }}>Loading investigations…</p>
                )}

                {selectedItem.kind === "election" && investigationsError && (
                  <div style={{ ...card, borderLeft: `4px solid ${theme.colors.status.error}`, marginBottom: theme.spacing.md }}>
                    <p style={{ ...cardText, margin: 0, color: theme.colors.status.error }}>{investigationsError}</p>
                  </div>
                )}

                {selectedItem.kind === "election" && !investigationsLoading && !investigationsError && (
                  <>
                    {investigations.length === 0 ? (
                      <div style={{ ...card, textAlign: "center", padding: theme.spacing.xl }}>
                        <p style={{ ...cardText, margin: 0, color: theme.colors.text.secondary }}>
                          No investigations found for this election.
                        </p>
                      </div>
                    ) : (
                      <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
                        {investigations.map((inv) => {
                          const assignee = inv.assigned_to
                            ? officialsList.find((o) => o.id === inv.assigned_to)
                            : null;
                          return (
                            <div key={inv.id} style={card}>
                              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: theme.spacing.sm }}>
                                <div>
                                  <h3 style={{ ...cardTitle, marginBottom: theme.spacing.xs }}>{inv.title}</h3>
                                  <p style={{ ...cardText, marginBottom: 0, fontSize: theme.fontSizes.sm }}>
                                    Severity: {inv.severity} · Raised {formatDateTime(inv.raised_at)}
                                    {inv.category && ` · ${inv.category.replace(/_/g, " ")}`}
                                  </p>
                                </div>
                                <div style={{ display: "flex", alignItems: "center", gap: theme.spacing.sm }}>
                                  <span style={getStatusBadgeStyle(theme, investStatusToBadge(inv.status))}>
                                    {inv.status.replace(/_/g, " ")}
                                  </span>
                                  <button
                                    type="button"
                                    onClick={() => openUpdateInvestigation(inv)}
                                    style={{ ...getTabButtonStyle(theme, false), padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}
                                  >
                                    Manage
                                  </button>
                                </div>
                              </div>
                              {inv.description && (
                                <p style={{ ...cardText, marginTop: theme.spacing.sm, marginBottom: 0 }}>
                                  {inv.description}
                                </p>
                              )}
                              {inv.notes && (
                                <p style={{ ...cardText, marginTop: theme.spacing.sm, marginBottom: 0, fontStyle: "italic", color: theme.colors.text.secondary }}>
                                  Notes: {inv.notes}
                                </p>
                              )}
                              {assignee && (
                                <p style={{ ...cardText, marginTop: theme.spacing.xs, marginBottom: 0, fontSize: theme.fontSizes.sm, color: theme.colors.text.secondary }}>
                                  Assigned to: {assignee.first_name} {assignee.last_name}
                                </p>
                              )}
                              {inv.resolution_summary && (
                                <div style={{ marginTop: theme.spacing.sm, padding: theme.spacing.sm, background: theme.colors.surfaceAlt, borderRadius: theme.borderRadius.md }}>
                                  <p style={{ ...cardText, marginBottom: 0, fontSize: theme.fontSizes.sm, fontWeight: theme.fontWeights.medium }}>
                                    Resolution summary
                                  </p>
                                  <p style={{ ...cardText, marginTop: theme.spacing.xs, marginBottom: 0, fontSize: theme.fontSizes.sm }}>
                                    {inv.resolution_summary}
                                  </p>
                                </div>
                              )}
                              {inv.resolved_at && (
                                <p style={{ ...cardText, marginTop: theme.spacing.xs, marginBottom: 0, fontSize: theme.fontSizes.sm, color: theme.colors.status.success }}>
                                  Resolved: {formatDateTime(inv.resolved_at)}
                                </p>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </>
                )}
              </section>
            )}

          </div>
        </>
      )}

      {!selectedItem && !itemsLoading && (
        <p style={{ paddingLeft: theme.spacing.xl, color: theme.colors.text.secondary }}>
          Select an election or referendum above to view the verification dashboard.
        </p>
      )}

      <ReportErrorModal
        open={reportErrorModalOpen}
        onClose={() => setReportErrorModalOpen(false)}
        onSubmitted={handleReportSubmitted}
        context={reportErrorContext}
        electionId={selectedItem?.kind === "election" ? selectedItem.id : undefined}
      />

      <UpdateInvestigationModal
        open={updateInvModalOpen}
        onClose={() => setUpdateInvModalOpen(false)}
        onUpdated={loadInvestigations}
        investigation={selectedInvestigation}
        officials={officialsList}
      />
    </div>
  );
};

export default OfficialHomePage;
