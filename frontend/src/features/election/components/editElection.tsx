import React, { useState, useEffect } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import {
  getCardStyle,
  getCardTextStyle,
  getH3Style,
  getStepFormInputStyle,
  getStepLabelStyle,
  getTabButtonStyle,
  getSelectStyle,
} from "../../../styles/ui";
import {
  Election,
  ElectionType,
  ElectionScope,
  ELECTION_TYPE_LABELS,
  UpdateElectionRequest,
} from "../model/election.model";
import { Constituency } from "../model/constituency.model";
import { ConstituencyApiRepository } from "../repositories/constituency-api.repository";
import { ElectionApiRepository } from "../repositories/election-api.repository";

interface EditElectionProps {
  open: boolean;
  election: Election | null;
  onClose: () => void;
  onUpdated: () => void;
}

interface FormState {
  title: string;
  election_type: string;
  scope: string;
  voting_opens: string;
  voting_closes: string;
  constituency_ids: string[];
}

function parseDmy(value: string): Date {
  const [dd, mm, yyyy] = value.split("/");
  return new Date(`${yyyy}-${mm}-${dd}T00:00:00`);
}

function isoToDmy(iso: string | undefined): string {
  if (!iso) return "";
  const d = new Date(iso);
  if (isNaN(d.getTime())) return "";
  const dd = String(d.getDate()).padStart(2, "0");
  const mm = String(d.getMonth() + 1).padStart(2, "0");
  const yyyy = d.getFullYear();
  return `${dd}/${mm}/${yyyy}`;
}

const SCOPE_OPTIONS: { value: ElectionScope; label: string }[] = [
  { value: ElectionScope.NATIONAL, label: "National" },
  { value: ElectionScope.REGIONAL, label: "Regional" },
  { value: ElectionScope.LOCAL, label: "Local" },
];

const constituencyApiRepository = new ConstituencyApiRepository();
const electionApiRepository = new ElectionApiRepository();

const EditElection: React.FC<EditElectionProps> = ({ open, election, onClose, onUpdated }) => {
  const { theme } = useTheme();
  const [form, setForm] = useState<FormState>({ title: "", election_type: "", scope: "", voting_opens: "", voting_closes: "", constituency_ids: [] });
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [constituencies, setConstituencies] = useState<Constituency[]>([]);
  const [constituencyFilter, setConstituencyFilter] = useState("");

  useEffect(() => {
    if (open && election) {
      setForm({
        title: election.title,
        election_type: election.election_type,
        scope: election.scope,
        voting_opens: isoToDmy(election.voting_opens),
        voting_closes: isoToDmy(election.voting_closes),
        constituency_ids: election.constituency_ids ?? [],
      });
      setErrors({});
      setSubmitError(null);
      constituencyApiRepository.listConstituencies()
        .then(setConstituencies)
        .catch(() => setConstituencies([]));
    }
  }, [open, election]);

  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);
  const labelStyle = { ...getStepLabelStyle(theme), display: "block" as const, marginBottom: theme.spacing.xs };
  const inputStyle = { ...getStepFormInputStyle(theme), boxSizing: "border-box" as const };

  if (!open || !election) return null;

  const filteredConstituencies = constituencies.filter(
    (c) => c.is_active && (constituencyFilter === "" || c.name.toLowerCase().includes(constituencyFilter.toLowerCase()) || c.country.toLowerCase().includes(constituencyFilter.toLowerCase())),
  );

  const validate = (): boolean => {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.title.trim()) next.title = "Required";
    if (!form.election_type) next.election_type = "Required";
    if (!form.scope) next.scope = "Required";
    const dateRe = /^\d{2}\/\d{2}\/\d{4}$/;
    if (form.voting_opens && !dateRe.test(form.voting_opens)) next.voting_opens = "Use dd/mm/yyyy format";
    else if (form.voting_opens && isNaN(parseDmy(form.voting_opens).getTime())) next.voting_opens = "Invalid date";
    if (form.voting_closes && !dateRe.test(form.voting_closes)) next.voting_closes = "Use dd/mm/yyyy format";
    else if (form.voting_closes && isNaN(parseDmy(form.voting_closes).getTime())) next.voting_closes = "Invalid date";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    setSubmitError(null);

    const body: UpdateElectionRequest = {
      title: form.title,
      election_type: form.election_type as ElectionType,
      scope: form.scope as ElectionScope,
      voting_opens: form.voting_opens ? parseDmy(form.voting_opens).toISOString() : undefined,
      voting_closes: form.voting_closes ? parseDmy(form.voting_closes).toISOString() : undefined,
      constituency_ids: form.constituency_ids,
    };

    try {
      await electionApiRepository.updateElection(election.id, body);
      onUpdated();
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Failed to update election.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => { setSubmitError(null); onClose(); };

  const toggleConstituency = (id: string) => {
    setForm((prev) => ({
      ...prev,
      constituency_ids: prev.constituency_ids.includes(id) ? prev.constituency_ids.filter((c) => c !== id) : [...prev.constituency_ids, id],
    }));
  };

  const selectAll = () => { setForm((prev) => ({ ...prev, constituency_ids: constituencies.filter((c) => c.is_active).map((c) => c.id) })); };
  const selectAllFiltered = () => { const ids = filteredConstituencies.map((c) => c.id); setForm((prev) => ({ ...prev, constituency_ids: Array.from(new Set([...prev.constituency_ids, ...ids])) })); };
  const clearConstituencies = () => { setForm((prev) => ({ ...prev, constituency_ids: [] })); };

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="edit-election-title"
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
      onClick={handleClose}>
      <div style={{ ...card, width: "100%", maxWidth: 640, margin: theme.spacing.xl, maxHeight: "90vh", overflowY: "auto" }}
        onClick={(e) => e.stopPropagation()}>
        <h3 id="edit-election-title" style={{ ...h3, marginBottom: theme.spacing.xs }}>Edit draft election</h3>
        <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>Update the election details. All fields are editable while in draft.</p>

        {submitError && (
          <div style={{ padding: theme.spacing.sm, marginBottom: theme.spacing.md, background: theme.colors.status.error + "15", borderLeft: `4px solid ${theme.colors.status.error}`, borderRadius: theme.borderRadius.sm }}>
            <p style={{ margin: 0, color: theme.colors.status.error, fontSize: theme.fontSizes.sm }}>{submitError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
            <div>
              <label htmlFor="ee-title" style={labelStyle}>Title</label>
              <input id="ee-title" type="text" value={form.title}
                onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
                style={{ ...inputStyle, borderColor: errors.title ? theme.colors.status.error : theme.colors.border }} autoComplete="off" />
              {errors.title && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.title}</p>}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: theme.spacing.md }}>
              <div>
                <label htmlFor="ee-type" style={labelStyle}>Election type</label>
                <select id="ee-type" value={form.election_type}
                  onChange={(e) => setForm((prev) => ({ ...prev, election_type: e.target.value }))}
                  style={{ ...getSelectStyle(theme), width: "100%", boxSizing: "border-box", borderColor: errors.election_type ? theme.colors.status.error : theme.colors.border }}>
                  <option value="">-- Select --</option>
                  {Object.entries(ELECTION_TYPE_LABELS).map(([val, label]) => (<option key={val} value={val}>{label}</option>))}
                </select>
                {errors.election_type && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.election_type}</p>}
              </div>
              <div>
                <label htmlFor="ee-scope" style={labelStyle}>Scope</label>
                <select id="ee-scope" value={form.scope}
                  onChange={(e) => setForm((prev) => ({ ...prev, scope: e.target.value }))}
                  style={{ ...getSelectStyle(theme), width: "100%", boxSizing: "border-box", borderColor: errors.scope ? theme.colors.status.error : theme.colors.border }}>
                  <option value="">-- Select --</option>
                  {SCOPE_OPTIONS.map((opt) => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
                </select>
                {errors.scope && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.scope}</p>}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: theme.spacing.md }}>
              <div>
                <label htmlFor="ee-opens" style={labelStyle}>Voting opens (dd/mm/yyyy)</label>
                <input id="ee-opens" type="text" placeholder="dd/mm/yyyy" value={form.voting_opens}
                  onChange={(e) => setForm((prev) => ({ ...prev, voting_opens: e.target.value }))}
                  style={{ ...inputStyle, borderColor: errors.voting_opens ? theme.colors.status.error : theme.colors.border }} autoComplete="off" />
                {errors.voting_opens && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.voting_opens}</p>}
              </div>
              <div>
                <label htmlFor="ee-closes" style={labelStyle}>Voting closes (dd/mm/yyyy)</label>
                <input id="ee-closes" type="text" placeholder="dd/mm/yyyy" value={form.voting_closes}
                  onChange={(e) => setForm((prev) => ({ ...prev, voting_closes: e.target.value }))}
                  style={{ ...inputStyle, borderColor: errors.voting_closes ? theme.colors.status.error : theme.colors.border }} autoComplete="off" />
                {errors.voting_closes && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.voting_closes}</p>}
              </div>
            </div>

            <div>
              <label style={labelStyle}>Constituencies ({form.constituency_ids.length} selected)</label>
              <div style={{ display: "flex", gap: theme.spacing.sm, marginBottom: theme.spacing.sm }}>
                <input type="text" placeholder="Filter by name or country..." value={constituencyFilter}
                  onChange={(e) => setConstituencyFilter(e.target.value)} style={{ ...inputStyle, flex: 1 }} />
                <button type="button" onClick={selectAll} style={{ ...getTabButtonStyle(theme, false), whiteSpace: "nowrap", fontSize: theme.fontSizes.xs }}>Select all</button>
                <button type="button" onClick={selectAllFiltered} style={{ ...getTabButtonStyle(theme, false), whiteSpace: "nowrap", fontSize: theme.fontSizes.xs }}>Select filtered</button>
                <button type="button" onClick={clearConstituencies} style={{ ...getTabButtonStyle(theme, false), whiteSpace: "nowrap", fontSize: theme.fontSizes.xs }}>Clear</button>
              </div>
              <div style={{ maxHeight: 180, overflowY: "auto", border: `1px solid ${theme.colors.border}`, borderRadius: theme.borderRadius.md, padding: theme.spacing.sm }}>
                {filteredConstituencies.length === 0 ? (
                  <p style={{ ...cardText, margin: 0, fontStyle: "italic", fontSize: theme.fontSizes.sm }}>No constituencies found.</p>
                ) : filteredConstituencies.map((c) => (
                  <label key={c.id} style={{ display: "flex", alignItems: "center", gap: theme.spacing.xs, padding: "2px 0", fontSize: theme.fontSizes.sm, cursor: "pointer" }}>
                    <input type="checkbox" checked={form.constituency_ids.includes(c.id)} onChange={() => toggleConstituency(c.id)} />
                    {c.name} ({c.country})
                  </label>
                ))}
              </div>
            </div>

            <div style={{ display: "flex", gap: theme.spacing.sm, justifyContent: "flex-end", paddingTop: theme.spacing.sm }}>
              <button type="button" onClick={handleClose} style={getTabButtonStyle(theme, false)} disabled={submitting}>Cancel</button>
              <button type="submit" disabled={submitting}
                style={{ ...getTabButtonStyle(theme, true), background: theme.colors.primary, color: theme.colors.text.inverse, opacity: submitting ? 0.6 : 1 }}>
                {submitting ? "Saving..." : "Save changes"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditElection;
