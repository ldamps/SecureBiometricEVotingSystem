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
import { Referendum, ReferendumScope, UpdateReferendumRequest } from "../model/referendum.model";
import { Constituency } from "../../election/model/constituency.model";
import { ConstituencyApiRepository } from "../../election/repositories/constituency-api.repository";
import { ReferendumApiRepository } from "../repositories/referendum-api.repository";

interface EditReferendumProps {
  open: boolean;
  referendum: Referendum | null;
  onClose: () => void;
  onUpdated: () => void;
}

interface FormState {
  title: string;
  question: string;
  description: string;
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

const SCOPE_OPTIONS: { value: ReferendumScope; label: string }[] = [
  { value: ReferendumScope.NATIONAL, label: "National" },
  { value: ReferendumScope.REGIONAL, label: "Regional" },
  { value: ReferendumScope.LOCAL, label: "Local" },
];

const constituencyApiRepository = new ConstituencyApiRepository();
const referendumApiRepository = new ReferendumApiRepository();

const EditReferendum: React.FC<EditReferendumProps> = ({ open, referendum, onClose, onUpdated }) => {
  const { theme } = useTheme();
  const [form, setForm] = useState<FormState>({ title: "", question: "", description: "", scope: "", voting_opens: "", voting_closes: "", constituency_ids: [] });
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [constituencies, setConstituencies] = useState<Constituency[]>([]);
  const [constituencyFilter, setConstituencyFilter] = useState("");

  useEffect(() => {
    if (open && referendum) {
      setForm({
        title: referendum.title,
        question: referendum.question,
        description: referendum.description ?? "",
        scope: referendum.scope,
        voting_opens: isoToDmy(referendum.voting_opens),
        voting_closes: isoToDmy(referendum.voting_closes),
        constituency_ids: referendum.constituency_ids ?? [],
      });
      setErrors({});
      setSubmitError(null);
      constituencyApiRepository.listConstituencies()
        .then(setConstituencies)
        .catch(() => setConstituencies([]));
    }
  }, [open, referendum]);

  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);
  const labelStyle = { ...getStepLabelStyle(theme), display: "block" as const, marginBottom: theme.spacing.xs };
  const inputStyle = { ...getStepFormInputStyle(theme), boxSizing: "border-box" as const };

  if (!open || !referendum) return null;

  const filteredConstituencies = constituencies.filter(
    (c) => c.is_active && (constituencyFilter === "" || c.name.toLowerCase().includes(constituencyFilter.toLowerCase()) || c.country.toLowerCase().includes(constituencyFilter.toLowerCase())),
  );

  const validate = (): boolean => {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.title.trim()) next.title = "Required";
    if (!form.question.trim()) next.question = "Required";
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

    const body: UpdateReferendumRequest = {
      title: form.title,
      question: form.question,
      description: form.description,
      scope: form.scope,
      voting_opens: form.voting_opens ? parseDmy(form.voting_opens).toISOString() : undefined,
      voting_closes: form.voting_closes ? parseDmy(form.voting_closes).toISOString() : undefined,
      constituency_ids: form.constituency_ids,
    };

    try {
      await referendumApiRepository.updateReferendum(referendum.id, body);
      onUpdated();
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : "Failed to update referendum.");
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
    <div role="dialog" aria-modal="true" aria-labelledby="edit-referendum-title"
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
      onClick={handleClose}>
      <div style={{ ...card, width: "100%", maxWidth: 640, margin: theme.spacing.xl, maxHeight: "90vh", overflowY: "auto" }}
        onClick={(e) => e.stopPropagation()}>
        <h3 id="edit-referendum-title" style={{ ...h3, marginBottom: theme.spacing.xs }}>Edit draft referendum</h3>
        <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>Update the referendum details. All fields are editable while in draft.</p>

        {submitError && (
          <div style={{ padding: theme.spacing.sm, marginBottom: theme.spacing.md, background: theme.colors.status.error + "15", borderLeft: `4px solid ${theme.colors.status.error}`, borderRadius: theme.borderRadius.sm }}>
            <p style={{ margin: 0, color: theme.colors.status.error, fontSize: theme.fontSizes.sm }}>{submitError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
            <div>
              <label htmlFor="er-title" style={labelStyle}>Title</label>
              <input id="er-title" type="text" value={form.title}
                onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
                style={{ ...inputStyle, borderColor: errors.title ? theme.colors.status.error : theme.colors.border }} autoComplete="off" />
              {errors.title && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.title}</p>}
            </div>

            <div>
              <label htmlFor="er-question" style={labelStyle}>Question</label>
              <textarea id="er-question" value={form.question} rows={3}
                onChange={(e) => setForm((prev) => ({ ...prev, question: e.target.value }))}
                style={{ ...inputStyle, resize: "vertical" as const, borderColor: errors.question ? theme.colors.status.error : theme.colors.border }} />
              {errors.question && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.question}</p>}
            </div>

            <div>
              <label htmlFor="er-desc" style={labelStyle}>Description (optional)</label>
              <textarea id="er-desc" value={form.description} rows={2}
                onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                style={{ ...inputStyle, resize: "vertical" as const }} />
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: theme.spacing.md }}>
              <div>
                <label htmlFor="er-scope" style={labelStyle}>Scope</label>
                <select id="er-scope" value={form.scope}
                  onChange={(e) => setForm((prev) => ({ ...prev, scope: e.target.value }))}
                  style={{ ...getSelectStyle(theme), width: "100%", boxSizing: "border-box", borderColor: errors.scope ? theme.colors.status.error : theme.colors.border }}>
                  <option value="">-- Select --</option>
                  {SCOPE_OPTIONS.map((opt) => (<option key={opt.value} value={opt.value}>{opt.label}</option>))}
                </select>
                {errors.scope && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.scope}</p>}
              </div>
              <div>
                <label htmlFor="er-opens" style={labelStyle}>Voting opens (dd/mm/yyyy)</label>
                <input id="er-opens" type="text" placeholder="dd/mm/yyyy" value={form.voting_opens}
                  onChange={(e) => setForm((prev) => ({ ...prev, voting_opens: e.target.value }))}
                  style={{ ...inputStyle, borderColor: errors.voting_opens ? theme.colors.status.error : theme.colors.border }} autoComplete="off" />
                {errors.voting_opens && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.voting_opens}</p>}
              </div>
              <div>
                <label htmlFor="er-closes" style={labelStyle}>Voting closes (dd/mm/yyyy)</label>
                <input id="er-closes" type="text" placeholder="dd/mm/yyyy" value={form.voting_closes}
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
              <div style={{ maxHeight: 160, overflowY: "auto", border: `1px solid ${theme.colors.border}`, borderRadius: theme.borderRadius.md, padding: theme.spacing.sm }}>
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

export default EditReferendum;
