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
import { ReferendumScope, ReferendumStatus, CreateReferendumRequest } from "../model/referendum.model";
import { Constituency } from "../../election/model/constituency.model";
import { ConstituencyApiRepository } from "../../election/repositories/constituency-api.repository";
import { ReferendumApiRepository } from "../repositories/referendum-api.repository";

interface CreateReferendumProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
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

/** Parse a dd/mm/yyyy string into a Date (start of day). */
function parseDmy(value: string): Date {
  const [dd, mm, yyyy] = value.split("/");
  return new Date(`${yyyy}-${mm}-${dd}T00:00:00`);
}

const BLANK_FORM: FormState = {
  title: "",
  question: "",
  description: "",
  scope: "",
  voting_opens: "",
  voting_closes: "",
  constituency_ids: [],
};

const SCOPE_OPTIONS: { value: ReferendumScope; label: string }[] = [
  { value: ReferendumScope.NATIONAL, label: "National" },
  { value: ReferendumScope.REGIONAL, label: "Regional" },
  { value: ReferendumScope.LOCAL, label: "Local" },
];

const constituencyApiRepository = new ConstituencyApiRepository();
const referendumApiRepository = new ReferendumApiRepository();

const CreateReferendum: React.FC<CreateReferendumProps> = ({ open, onClose, onCreated }) => {
  const { theme } = useTheme();
  const [form, setForm] = useState<FormState>(BLANK_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const [constituencies, setConstituencies] = useState<Constituency[]>([]);
  const [constituencyFilter, setConstituencyFilter] = useState("");

  useEffect(() => {
    if (open) {
      constituencyApiRepository.listConstituencies()
        .then(setConstituencies)
        .catch(() => setConstituencies([]));
    }
  }, [open]);

  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);

  const labelStyle = {
    ...getStepLabelStyle(theme),
    display: "block" as const,
    marginBottom: theme.spacing.xs,
  };

  const inputStyle = {
    ...getStepFormInputStyle(theme),
    boxSizing: "border-box" as const,
  };

  if (!open) return null;

  const filteredConstituencies = constituencies.filter(
    (c) =>
      c.is_active &&
      (constituencyFilter === "" ||
        c.name.toLowerCase().includes(constituencyFilter.toLowerCase()) ||
        c.country.toLowerCase().includes(constituencyFilter.toLowerCase())),
  );

  const validate = (isDraft: boolean): boolean => {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.title.trim()) next.title = "Required";
    if (!form.question.trim()) next.question = "Required";
    if (!form.scope) next.scope = "Required";
    if (!isDraft) {
      const dateRe = /^\d{2}\/\d{2}\/\d{4}$/;
      if (!form.voting_opens) {
        next.voting_opens = "Required";
      } else if (!dateRe.test(form.voting_opens)) {
        next.voting_opens = "Use dd/mm/yyyy format";
      } else if (isNaN(parseDmy(form.voting_opens).getTime())) {
        next.voting_opens = "Invalid date";
      }
      if (!form.voting_closes) {
        next.voting_closes = "Required";
      } else if (!dateRe.test(form.voting_closes)) {
        next.voting_closes = "Use dd/mm/yyyy format";
      } else if (isNaN(parseDmy(form.voting_closes).getTime())) {
        next.voting_closes = "Invalid date";
      }
      if (!next.voting_opens && !next.voting_closes && parseDmy(form.voting_opens) >= parseDmy(form.voting_closes)) {
        next.voting_closes = "Must be after voting opens";
      }
    } else {
      const dateRe = /^\d{2}\/\d{2}\/\d{4}$/;
      if (form.voting_opens && !dateRe.test(form.voting_opens)) {
        next.voting_opens = "Use dd/mm/yyyy format";
      } else if (form.voting_opens && isNaN(parseDmy(form.voting_opens).getTime())) {
        next.voting_opens = "Invalid date";
      }
      if (form.voting_closes && !dateRe.test(form.voting_closes)) {
        next.voting_closes = "Use dd/mm/yyyy format";
      } else if (form.voting_closes && isNaN(parseDmy(form.voting_closes).getTime())) {
        next.voting_closes = "Invalid date";
      }
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const submitForm = async (isDraft: boolean) => {
    if (!validate(isDraft)) return;

    setSubmitting(true);
    setSubmitError(null);

    const body: CreateReferendumRequest = {
      title: form.title,
      question: form.question,
      description: form.description,
      scope: form.scope as ReferendumScope,
      ...(isDraft ? { status: ReferendumStatus.DRAFT } : {}),
      voting_opens: form.voting_opens ? parseDmy(form.voting_opens).toISOString() : undefined,
      voting_closes: form.voting_closes ? parseDmy(form.voting_closes).toISOString() : undefined,
      constituency_ids: form.constituency_ids,
    };

    try {
      await referendumApiRepository.createReferendum(body);
      setForm(BLANK_FORM);
      setErrors({});
      onCreated();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to create referendum.";
      setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    await submitForm(false);
  };

  const handleClose = () => {
    setForm(BLANK_FORM);
    setErrors({});
    setSubmitError(null);
    onClose();
  };

  const toggleConstituency = (id: string) => {
    setForm((prev) => ({
      ...prev,
      constituency_ids: prev.constituency_ids.includes(id)
        ? prev.constituency_ids.filter((c) => c !== id)
        : [...prev.constituency_ids, id],
    }));
  };

  const selectAll = () => {
    const ids = constituencies.filter((c) => c.is_active).map((c) => c.id);
    setForm((prev) => ({ ...prev, constituency_ids: ids }));
  };

  const selectAllFiltered = () => {
    const ids = filteredConstituencies.map((c) => c.id);
    setForm((prev) => ({
      ...prev,
      constituency_ids: Array.from(new Set([...prev.constituency_ids, ...ids])),
    }));
  };

  const clearConstituencies = () => {
    setForm((prev) => ({ ...prev, constituency_ids: [] }));
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="create-referendum-title"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(0,0,0,0.4)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 1000,
      }}
      onClick={handleClose}
    >
      <div
        style={{
          ...card,
          width: "100%",
          maxWidth: 640,
          margin: theme.spacing.xl,
          maxHeight: "90vh",
          overflowY: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="create-referendum-title" style={{ ...h3, marginBottom: theme.spacing.xs }}>
          Create new referendum
        </h3>
        <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
          Set up a new yes/no referendum question for voters.
        </p>

        {submitError && (
          <div style={{ padding: theme.spacing.sm, marginBottom: theme.spacing.md, background: theme.colors.status.error + "15", borderLeft: `4px solid ${theme.colors.status.error}`, borderRadius: theme.borderRadius.sm }}>
            <p style={{ margin: 0, color: theme.colors.status.error, fontSize: theme.fontSizes.sm }}>{submitError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
            {/* Title */}
            <div>
              <label htmlFor="cr-title" style={labelStyle}>Title</label>
              <input
                id="cr-title"
                type="text"
                placeholder="e.g. National Voting Age Referendum"
                value={form.title}
                onChange={(e) => setForm((prev) => ({ ...prev, title: e.target.value }))}
                style={{ ...inputStyle, borderColor: errors.title ? theme.colors.status.error : theme.colors.border }}
                autoComplete="off"
              />
              {errors.title && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.title}</p>}
            </div>

            {/* Question */}
            <div>
              <label htmlFor="cr-question" style={labelStyle}>Question</label>
              <textarea
                id="cr-question"
                placeholder="The yes/no question presented to voters..."
                value={form.question}
                onChange={(e) => setForm((prev) => ({ ...prev, question: e.target.value }))}
                rows={3}
                style={{
                  ...inputStyle,
                  resize: "vertical" as const,
                  borderColor: errors.question ? theme.colors.status.error : theme.colors.border,
                }}
              />
              {errors.question && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.question}</p>}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="cr-desc" style={labelStyle}>Description (optional)</label>
              <textarea
                id="cr-desc"
                placeholder="Additional context about the referendum..."
                value={form.description}
                onChange={(e) => setForm((prev) => ({ ...prev, description: e.target.value }))}
                rows={2}
                style={{ ...inputStyle, resize: "vertical" as const }}
              />
            </div>

            {/* Scope + Voting window */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: theme.spacing.md }}>
              <div>
                <label htmlFor="cr-scope" style={labelStyle}>Scope</label>
                <select
                  id="cr-scope"
                  value={form.scope}
                  onChange={(e) => setForm((prev) => ({ ...prev, scope: e.target.value }))}
                  style={{ ...getSelectStyle(theme), width: "100%", boxSizing: "border-box", borderColor: errors.scope ? theme.colors.status.error : theme.colors.border }}
                >
                  <option value="">-- Select --</option>
                  {SCOPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                  ))}
                </select>
                {errors.scope && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.scope}</p>}
              </div>
              <div>
                <label htmlFor="cr-opens" style={labelStyle}>Voting opens (dd/mm/yyyy)</label>
                <input
                  id="cr-opens"
                  type="text"
                  placeholder="dd/mm/yyyy"
                  value={form.voting_opens}
                  onChange={(e) => setForm((prev) => ({ ...prev, voting_opens: e.target.value }))}
                  style={{ ...inputStyle, borderColor: errors.voting_opens ? theme.colors.status.error : theme.colors.border }}
                  autoComplete="off"
                />
                {errors.voting_opens && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.voting_opens}</p>}
              </div>
              <div>
                <label htmlFor="cr-closes" style={labelStyle}>Voting closes (dd/mm/yyyy)</label>
                <input
                  id="cr-closes"
                  type="text"
                  placeholder="dd/mm/yyyy"
                  value={form.voting_closes}
                  onChange={(e) => setForm((prev) => ({ ...prev, voting_closes: e.target.value }))}
                  style={{ ...inputStyle, borderColor: errors.voting_closes ? theme.colors.status.error : theme.colors.border }}
                  autoComplete="off"
                />
                {errors.voting_closes && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.voting_closes}</p>}
              </div>
            </div>

            {/* Constituencies */}
            <div>
              <label style={labelStyle}>
                Constituencies ({form.constituency_ids.length} selected)
              </label>
              <div style={{ display: "flex", gap: theme.spacing.sm, marginBottom: theme.spacing.sm }}>
                <input
                  type="text"
                  placeholder="Filter by name or country..."
                  value={constituencyFilter}
                  onChange={(e) => setConstituencyFilter(e.target.value)}
                  style={{ ...inputStyle, flex: 1 }}
                />
                <button type="button" onClick={selectAll} style={{ ...getTabButtonStyle(theme, false), whiteSpace: "nowrap", fontSize: theme.fontSizes.xs }}>
                  Select all
                </button>
                <button type="button" onClick={selectAllFiltered} style={{ ...getTabButtonStyle(theme, false), whiteSpace: "nowrap", fontSize: theme.fontSizes.xs }}>
                  Select filtered
                </button>
                <button type="button" onClick={clearConstituencies} style={{ ...getTabButtonStyle(theme, false), whiteSpace: "nowrap", fontSize: theme.fontSizes.xs }}>
                  Clear
                </button>
              </div>
              <div style={{
                maxHeight: 160,
                overflowY: "auto",
                border: `1px solid ${theme.colors.border}`,
                borderRadius: theme.borderRadius.md,
                padding: theme.spacing.sm,
              }}>
                {filteredConstituencies.length === 0 ? (
                  <p style={{ ...cardText, margin: 0, fontStyle: "italic", fontSize: theme.fontSizes.sm }}>No constituencies found.</p>
                ) : (
                  filteredConstituencies.map((c) => (
                    <label key={c.id} style={{ display: "flex", alignItems: "center", gap: theme.spacing.xs, padding: `2px 0`, fontSize: theme.fontSizes.sm, cursor: "pointer" }}>
                      <input
                        type="checkbox"
                        checked={form.constituency_ids.includes(c.id)}
                        onChange={() => toggleConstituency(c.id)}
                      />
                      {c.name} ({c.country})
                    </label>
                  ))
                )}
              </div>
            </div>

            {/* Actions */}
            <div style={{ display: "flex", gap: theme.spacing.sm, justifyContent: "flex-end", paddingTop: theme.spacing.sm }}>
              <button type="button" onClick={handleClose} style={getTabButtonStyle(theme, false)} disabled={submitting}>
                Cancel
              </button>
              <button
                type="button"
                disabled={submitting}
                onClick={() => submitForm(true)}
                style={{
                  ...getTabButtonStyle(theme, false),
                  opacity: submitting ? 0.6 : 1,
                }}
              >
                {submitting ? "Saving..." : "Save as draft"}
              </button>
              <button
                type="submit"
                disabled={submitting}
                style={{
                  ...getTabButtonStyle(theme, true),
                  background: theme.colors.primary,
                  color: theme.colors.text.inverse,
                  opacity: submitting ? 0.6 : 1,
                }}
              >
                {submitting ? "Creating..." : "Create referendum"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default CreateReferendum;
