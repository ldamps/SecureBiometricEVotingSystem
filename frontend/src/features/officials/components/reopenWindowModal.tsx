import React, { useEffect, useState } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import {
  getCardStyle,
  getCardTextStyle,
  getH3Style,
  getStepFormInputStyle,
  getStepLabelStyle,
  getTabButtonStyle,
} from "../../../styles/ui";

interface ReopenWindowModalProps {
  open: boolean;
  kind: "election" | "referendum";
  title: string;
  currentVotingOpens?: string;
  currentVotingCloses?: string;
  onClose: () => void;
  onConfirm: (votingOpensIso: string | undefined, votingClosesIso: string) => Promise<void> | void;
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

function todayDmy(): string {
  return isoToDmy(new Date().toISOString());
}

const DATE_RE = /^\d{2}\/\d{2}\/\d{4}$/;

const ReopenWindowModal: React.FC<ReopenWindowModalProps> = ({
  open,
  kind,
  title,
  currentVotingOpens,
  currentVotingCloses,
  onClose,
  onConfirm,
}) => {
  const { theme } = useTheme();
  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);
  const labelStyle = { ...getStepLabelStyle(theme), display: "block" as const, marginBottom: theme.spacing.xs };
  const inputStyle = { ...getStepFormInputStyle(theme), boxSizing: "border-box" as const, width: "100%" };

  const [opensValue, setOpensValue] = useState("");
  const [closesValue, setClosesValue] = useState("");
  const [errors, setErrors] = useState<{ opens?: string; closes?: string }>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setOpensValue(isoToDmy(currentVotingOpens) || todayDmy());
      setClosesValue("");
      setErrors({});
      setSubmitError(null);
    }
  }, [open, currentVotingOpens, currentVotingCloses]);

  if (!open) return null;

  const validate = (): { opensIso?: string; closesIso?: string } | null => {
    const next: { opens?: string; closes?: string } = {};
    let opensIso: string | undefined;
    let closesIso: string | undefined;

    if (opensValue) {
      if (!DATE_RE.test(opensValue)) next.opens = "Use dd/mm/yyyy format";
      else {
        const d = parseDmy(opensValue);
        if (isNaN(d.getTime())) next.opens = "Invalid date";
        else opensIso = d.toISOString();
      }
    }

    if (!closesValue) next.closes = "Required";
    else if (!DATE_RE.test(closesValue)) next.closes = "Use dd/mm/yyyy format";
    else {
      const d = parseDmy(closesValue);
      if (isNaN(d.getTime())) next.closes = "Invalid date";
      else {
        const endOfDay = new Date(d);
        endOfDay.setHours(23, 59, 59, 999);
        if (endOfDay.getTime() <= Date.now()) next.closes = "Must be in the future";
        else closesIso = endOfDay.toISOString();
      }
    }

    if (!next.opens && !next.closes && opensIso && closesIso && new Date(opensIso) >= new Date(closesIso)) {
      next.closes = "Must be after voting opens";
    }

    setErrors(next);
    if (Object.keys(next).length > 0) return null;
    return { opensIso, closesIso };
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const parsed = validate();
    if (!parsed || !parsed.closesIso) return;
    setSubmitting(true);
    setSubmitError(null);
    try {
      await onConfirm(parsed.opensIso, parsed.closesIso);
    } catch (err: unknown) {
      setSubmitError(err instanceof Error ? err.message : `Failed to reopen ${kind}.`);
      setSubmitting(false);
      return;
    }
    setSubmitting(false);
  };

  return (
    <div role="dialog" aria-modal="true" aria-labelledby="reopen-window-title"
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
      onClick={onClose}>
      <div style={{ ...card, width: "100%", maxWidth: 480, margin: theme.spacing.xl, maxHeight: "90vh", overflowY: "auto" }}
        onClick={(e) => e.stopPropagation()}>
        <h3 id="reopen-window-title" style={{ ...h3, marginBottom: theme.spacing.xs }}>
          Reopen {kind}
        </h3>
        <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
          Confirm the new voting window for <strong>{title}</strong>. Voting closes is required so the {kind} does not stay open indefinitely.
        </p>

        {submitError && (
          <div style={{ padding: theme.spacing.sm, marginBottom: theme.spacing.md, background: theme.colors.status.error + "15", borderLeft: `4px solid ${theme.colors.status.error}`, borderRadius: theme.borderRadius.sm }}>
            <p style={{ margin: 0, color: theme.colors.status.error, fontSize: theme.fontSizes.sm }}>{submitError}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
            <div>
              <label htmlFor="rw-opens" style={labelStyle}>Voting opens (dd/mm/yyyy)</label>
              <input id="rw-opens" type="text" placeholder="dd/mm/yyyy" value={opensValue}
                onChange={(e) => setOpensValue(e.target.value)} autoComplete="off"
                style={{ ...inputStyle, borderColor: errors.opens ? theme.colors.status.error : theme.colors.border }} />
              {errors.opens && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.opens}</p>}
            </div>
            <div>
              <label htmlFor="rw-closes" style={labelStyle}>Voting closes (dd/mm/yyyy)</label>
              <input id="rw-closes" type="text" placeholder="dd/mm/yyyy" value={closesValue}
                onChange={(e) => setClosesValue(e.target.value)} autoComplete="off"
                style={{ ...inputStyle, borderColor: errors.closes ? theme.colors.status.error : theme.colors.border }} />
              {errors.closes && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.closes}</p>}
            </div>

            <div style={{ display: "flex", gap: theme.spacing.sm, justifyContent: "flex-end", paddingTop: theme.spacing.sm }}>
              <button type="button" onClick={onClose} style={getTabButtonStyle(theme, false)} disabled={submitting}>Cancel</button>
              <button type="submit" disabled={submitting}
                style={{ ...getTabButtonStyle(theme, true), background: theme.colors.status.success, color: theme.colors.text.inverse, opacity: submitting ? 0.6 : 1 }}>
                {submitting ? "Reopening..." : "Reopen"}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ReopenWindowModal;
