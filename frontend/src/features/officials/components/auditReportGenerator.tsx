// auditReportGenerator.tsx - Generates a PDF audit report from aggregated, privacy-safe data.

import jsPDF from "jspdf";
import autoTable from "jspdf-autotable";
import type {
    BallotReconciliationSummary,
    BiometricVerificationSummary,
    ElectionAuditReport,
    ReferendumAuditReport,
    VotingPeriodIntegrity,
} from "../model/audit-report.model";

function formatDate(iso: string | null): string {
    if (!iso) return "N/A";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
}

function addHeader(doc: jsPDF, title: string, y: number): number {
    doc.setFontSize(18);
    doc.setFont("helvetica", "bold");
    doc.text(title, 14, y);
    y += 4;
    doc.setLineWidth(0.5);
    doc.line(14, y, 196, y);
    return y + 8;
}

function addSectionTitle(doc: jsPDF, title: string, y: number): number {
    if (y > 260) { doc.addPage(); y = 20; }
    doc.setFontSize(13);
    doc.setFont("helvetica", "bold");
    doc.text(title, 14, y);
    return y + 7;
}

function addKeyValue(doc: jsPDF, key: string, value: string, y: number): number {
    if (y > 275) { doc.addPage(); y = 20; }
    doc.setFontSize(10);
    doc.setFont("helvetica", "bold");
    doc.text(`${key}:`, 14, y);
    doc.setFont("helvetica", "normal");
    doc.text(value, 60, y);
    return y + 6;
}

function addBallotReconciliation(doc: jsPDF, recon: BallotReconciliationSummary, y: number): number {
    if (y > 220) { doc.addPage(); y = 20; }
    y = addSectionTitle(doc, "Ballot reconciliation", y);
    y = addKeyValue(doc, "Tokens issued", recon.tokens_issued.toLocaleString(), y);
    y = addKeyValue(doc, "Tokens used", recon.tokens_used.toLocaleString(), y);
    y = addKeyValue(doc, "Votes recorded", recon.votes_recorded.toLocaleString(), y);
    y = addKeyValue(doc, "Ledger entries", recon.voter_ledger_entries.toLocaleString(), y);
    y = addKeyValue(doc, "Reconciled", recon.fully_reconciled ? "YES — all figures match" : "NO — discrepancy detected", y);

    if (recon.per_constituency.length > 0) {
        y += 2;
        autoTable(doc, {
            startY: y,
            head: [["Constituency", "Tokens issued", "Tokens used", "Votes recorded"]],
            body: recon.per_constituency.map((c) => [
                c.constituency_name,
                c.tokens_issued.toLocaleString(),
                c.tokens_used.toLocaleString(),
                c.votes_recorded.toLocaleString(),
            ]),
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    } else {
        y += 4;
    }
    return y;
}

function addVotingPeriodIntegrity(doc: jsPDF, vp: VotingPeriodIntegrity, y: number): number {
    if (y > 240) { doc.addPage(); y = 20; }
    y = addSectionTitle(doc, "Voting period integrity", y);
    y = addKeyValue(doc, "Window opens", formatDate(vp.voting_opens), y);
    y = addKeyValue(doc, "Window closes", formatDate(vp.voting_closes), y);
    y = addKeyValue(doc, "Earliest vote", formatDate(vp.earliest_vote), y);
    y = addKeyValue(doc, "Latest vote", formatDate(vp.latest_vote), y);
    y = addKeyValue(doc, "All within window", vp.all_votes_within_window ? "YES" : "NO — votes detected outside window", y);
    y += 4;
    return y;
}

function addBiometricSummary(doc: jsPDF, bio: BiometricVerificationSummary, y: number): number {
    if (y > 240) { doc.addPage(); y = 20; }
    y = addSectionTitle(doc, "Biometric verification summary", y);
    y = addKeyValue(doc, "Challenges issued", bio.challenges_issued.toLocaleString(), y);
    y = addKeyValue(doc, "Completed", bio.challenges_completed.toLocaleString(), y);
    y = addKeyValue(doc, "Expired", bio.challenges_expired.toLocaleString(), y);
    y += 4;
    return y;
}

export function generateElectionAuditPdf(
    report: ElectionAuditReport,
    partyMap: Record<string, { party_name?: string; abbreviation?: string }>,
): void {
    const doc = new jsPDF();
    let y = 20;

    // Title
    y = addHeader(doc, "Election audit report", y);

    // Metadata
    y = addSectionTitle(doc, "Election details", y);
    y = addKeyValue(doc, "Title", report.title, y);
    y = addKeyValue(doc, "Type", report.election_type, y);
    y = addKeyValue(doc, "Allocation", report.allocation_method, y);
    y = addKeyValue(doc, "Scope", report.scope, y);
    y = addKeyValue(doc, "Status", report.status, y);
    y = addKeyValue(doc, "Voting opens", formatDate(report.voting_opens), y);
    y = addKeyValue(doc, "Voting closes", formatDate(report.voting_closes), y);
    y = addKeyValue(doc, "Created", formatDate(report.created_at), y);
    y += 4;

    // Turnout summary
    y = addSectionTitle(doc, "Turnout summary", y);
    y = addKeyValue(doc, "Total votes cast", report.total_votes_cast.toLocaleString(), y);
    y = addKeyValue(doc, "Constituencies", report.total_constituencies.toString(), y);
    y += 4;

    // Ballot reconciliation
    y = addBallotReconciliation(doc, report.ballot_reconciliation, y);

    // Voting period integrity
    y = addVotingPeriodIntegrity(doc, report.voting_period_integrity, y);

    // Biometric verification
    y = addBiometricSummary(doc, report.biometric_summary, y);

    // Result summary
    y = addSectionTitle(doc, "Result summary", y);
    y = addKeyValue(doc, "Total seats", report.total_seats.toString(), y);
    y = addKeyValue(doc, "Majority threshold", report.majority_threshold.toString(), y);
    const winnerName = report.winning_party_id
        ? (partyMap[report.winning_party_id]?.party_name ?? report.winning_party_id.slice(0, 8))
        : "No majority";
    y = addKeyValue(doc, "Winning party", winnerName, y);
    y += 4;

    // Seat allocation table
    const seatRows = Object.entries(report.seat_allocation).map(([pid, seats]) => [
        partyMap[pid]?.party_name ?? partyMap[pid]?.abbreviation ?? pid.slice(0, 8),
        seats.toString(),
    ]);
    if (seatRows.length > 0) {
        y = addSectionTitle(doc, "Seat allocation by party", y);
        autoTable(doc, {
            startY: y,
            head: [["Party", "Seats"]],
            body: seatRows,
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    }

    // Constituency turnout table
    if (report.constituency_turnout.length > 0) {
        if (y > 220) { doc.addPage(); y = 20; }
        y = addSectionTitle(doc, "Constituency turnout", y);
        autoTable(doc, {
            startY: y,
            head: [["Constituency", "Votes cast"]],
            body: report.constituency_turnout.map((c) => [
                c.constituency_name,
                c.votes_cast.toLocaleString(),
            ]),
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    }

    // Event counts
    const eventEntries = Object.entries(report.event_counts);
    if (eventEntries.length > 0) {
        if (y > 220) { doc.addPage(); y = 20; }
        y = addSectionTitle(doc, "Aggregate event counts", y);
        autoTable(doc, {
            startY: y,
            head: [["Event type", "Count"]],
            body: eventEntries.map(([type, count]) => [
                type.replace(/_/g, " "),
                count.toString(),
            ]),
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    }

    // System timeline
    if (report.timeline.length > 0) {
        if (y > 220) { doc.addPage(); y = 20; }
        y = addSectionTitle(doc, "System event timeline", y);
        autoTable(doc, {
            startY: y,
            head: [["Timestamp", "Event", "Summary"]],
            body: report.timeline.map((e) => [
                formatDate(e.timestamp),
                e.event_type.replace(/_/g, " "),
                e.summary,
            ]),
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
            columnStyles: { 2: { cellWidth: 80 } },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    }

    // Investigations
    if (report.investigations.length > 0) {
        if (y > 220) { doc.addPage(); y = 20; }
        y = addSectionTitle(doc, "Investigations", y);
        autoTable(doc, {
            startY: y,
            head: [["Title", "Severity", "Status", "Raised", "Resolved"]],
            body: report.investigations.map((inv) => [
                inv.title,
                inv.severity,
                inv.status.replace(/_/g, " "),
                formatDate(inv.raised_at),
                formatDate(inv.resolved_at),
            ]),
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    }

    // Footer
    if (y > 260) { doc.addPage(); y = 20; }
    y += 4;
    doc.setLineWidth(0.3);
    doc.line(14, y, 196, y);
    y += 6;
    doc.setFontSize(9);
    doc.setFont("helvetica", "italic");
    doc.text(`Report generated: ${formatDate(report.generated_at)}`, 14, y);
    y += 5;
    if (report.generated_by) {
        doc.text(`Generated by official: ${report.generated_by}`, 14, y);
        y += 5;
    }
    doc.text("This report contains no voter-identifiable information.", 14, y);

    const safeName = report.title.replace(/[^a-zA-Z0-9]/g, "_").slice(0, 40);
    doc.save(`audit_report_${safeName}.pdf`);
}

export function generateReferendumAuditPdf(report: ReferendumAuditReport): void {
    const doc = new jsPDF();
    let y = 20;

    y = addHeader(doc, "Referendum audit report", y);

    y = addSectionTitle(doc, "Referendum details", y);
    y = addKeyValue(doc, "Title", report.title, y);
    y = addKeyValue(doc, "Question", report.question, y);
    y = addKeyValue(doc, "Scope", report.scope, y);
    y = addKeyValue(doc, "Status", report.status, y);
    y = addKeyValue(doc, "Voting opens", formatDate(report.voting_opens), y);
    y = addKeyValue(doc, "Voting closes", formatDate(report.voting_closes), y);
    y = addKeyValue(doc, "Created", formatDate(report.created_at), y);
    y += 4;

    y = addSectionTitle(doc, "Result summary", y);
    y = addKeyValue(doc, "Total votes cast", report.total_votes_cast.toLocaleString(), y);
    y = addKeyValue(doc, "Yes votes", report.yes_votes.toLocaleString(), y);
    y = addKeyValue(doc, "No votes", report.no_votes.toLocaleString(), y);
    y = addKeyValue(doc, "Outcome", report.outcome, y);
    if (report.total_votes_cast > 0) {
        y = addKeyValue(doc, "Yes %", ((report.yes_votes / report.total_votes_cast) * 100).toFixed(1) + "%", y);
        y = addKeyValue(doc, "No %", ((report.no_votes / report.total_votes_cast) * 100).toFixed(1) + "%", y);
    }
    y += 4;

    // Ballot reconciliation
    y = addBallotReconciliation(doc, report.ballot_reconciliation, y);

    // Voting period integrity
    y = addVotingPeriodIntegrity(doc, report.voting_period_integrity, y);

    // Biometric verification
    y = addBiometricSummary(doc, report.biometric_summary, y);

    // Event counts
    const eventEntries = Object.entries(report.event_counts);
    if (eventEntries.length > 0) {
        y = addSectionTitle(doc, "Aggregate event counts", y);
        autoTable(doc, {
            startY: y,
            head: [["Event type", "Count"]],
            body: eventEntries.map(([type, count]) => [
                type.replace(/_/g, " "),
                count.toString(),
            ]),
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    }

    // System timeline
    if (report.timeline.length > 0) {
        if (y > 220) { doc.addPage(); y = 20; }
        y = addSectionTitle(doc, "System event timeline", y);
        autoTable(doc, {
            startY: y,
            head: [["Timestamp", "Event", "Summary"]],
            body: report.timeline.map((e) => [
                formatDate(e.timestamp),
                e.event_type.replace(/_/g, " "),
                e.summary,
            ]),
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
            columnStyles: { 2: { cellWidth: 80 } },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    }

    // Investigations
    if (report.investigations.length > 0) {
        if (y > 220) { doc.addPage(); y = 20; }
        y = addSectionTitle(doc, "Investigations", y);
        autoTable(doc, {
            startY: y,
            head: [["Title", "Severity", "Status", "Raised", "Resolved"]],
            body: report.investigations.map((inv) => [
                inv.title,
                inv.severity,
                inv.status.replace(/_/g, " "),
                formatDate(inv.raised_at),
                formatDate(inv.resolved_at),
            ]),
            theme: "grid",
            headStyles: { fillColor: [41, 65, 122] },
            margin: { left: 14, right: 14 },
        });
        y = (doc as jsPDF & { lastAutoTable: { finalY: number } }).lastAutoTable.finalY + 8;
    }

    // Footer
    if (y > 260) { doc.addPage(); y = 20; }
    y += 4;
    doc.setLineWidth(0.3);
    doc.line(14, y, 196, y);
    y += 6;
    doc.setFontSize(9);
    doc.setFont("helvetica", "italic");
    doc.text(`Report generated: ${formatDate(report.generated_at)}`, 14, y);
    y += 5;
    if (report.generated_by) {
        doc.text(`Generated by official: ${report.generated_by}`, 14, y);
        y += 5;
    }
    doc.text("This report contains no voter-identifiable information.", 14, y);

    const safeName = report.title.replace(/[^a-zA-Z0-9]/g, "_").slice(0, 40);
    doc.save(`audit_report_${safeName}.pdf`);
}
