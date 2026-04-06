import React, { useState } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import {
  getCardStyle,
  getCardTextStyle,
  getH3Style,
  getStepFormInputStyle,
  getStepLabelStyle,
  getSelectStyle,
  getTabButtonStyle,
} from "../../../styles/ui";
import { InvestigationApiRepository } from "../../investigation/repositories/investigation-api.repository";
import { getAccessTokenSubject } from "../../../services/api-client.service";

const investigationApiRepository = new InvestigationApiRepository();

const SEVERITY_OPTIONS = ["LOW", "MEDIUM", "HIGH", "CRITICAL"] as const;

interface ReportErrorModalProps {
  open: boolean;
  onClose: () => void;
  onSubmitted?: () => void;
  context?: string | null;
  electionId?: string;
}

const ReportErrorModal: React.FC<ReportErrorModalProps> = ({ open, onClose, onSubmitted, context = null, electionId }) => {
  const { theme } = useTheme();
  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);

  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  if (!open) return null;

  const validate = (): boolean => {
    const next: Record<string, string> = {};
    if (!title.trim() || title.trim().length < 3) next.title = "Title is required (min 3 characters)";
    if (!severity) next.severity = "Please select a severity level";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    if (!electionId) {
      setSubmitError("No election selected. Error reports can only be filed for elections.");
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    const officialId = getAccessTokenSubject();
    await investigationApiRepository.createErrorReport({
      election_id: electionId,
      reported_by: officialId ?? undefined,
      title: context ? `${context} — ${title}` : title,
      description: description || undefined,
      severity,
    })
      .then(() => {
        setTitle("");
        setDescription("");
        setSeverity("");
        setErrors({});
        onSubmitted?.();
      })
      .catch((err: Error) => {
        setSubmitError(err.message || "Failed to submit error report.");
      })
      .finally(() => setSubmitting(false));
  };

  const handleClose = () => {
    setTitle("");
    setDescription("");
    setSeverity("");
    setErrors({});
    setSubmitError(null);
    onClose();
  };

  const labelStyle = {
    ...getStepLabelStyle(theme),
    display: "block" as const,
    marginBottom: theme.spacing.xs,
  };

  const inputStyle = {
    ...getStepFormInputStyle(theme),
    boxSizing: "border-box" as const,
    width: "100%",
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="report-error-title"
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
          maxWidth: 480,
          margin: theme.spacing.xl,
          maxHeight: "90vh",
          overflow: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="report-error-title" style={h3}>
          Report an error
        </h3>
        {context && (
          <p style={{ ...cardText, marginBottom: theme.spacing.sm }}>
            Context: <strong>{context}</strong>
          </p>
        )}
        <p style={{ ...cardText, marginBottom: theme.spacing.md }}>
          Report discrepancies or issues you have identified. An investigation will be automatically opened.
        </p>

        {submitError && (
          <p style={{ ...cardText, color: theme.colors.status.error, marginBottom: theme.spacing.md }}>
            {submitError}
          </p>
        )}

        <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
          <div>
            <label style={labelStyle}>Severity</label>
            <select
              value={severity}
              onChange={(e) => setSeverity(e.target.value)}
              style={{
                ...getSelectStyle(theme),
                width: "100%",
                boxSizing: "border-box",
                borderColor: errors.severity ? theme.colors.status.error : theme.colors.border,
              }}
            >
              <option value="">— Select severity —</option>
              {SEVERITY_OPTIONS.map((s) => (
                <option key={s} value={s}>{s}</option>
              ))}
            </select>
            {errors.severity && (
              <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>
                {errors.severity}
              </p>
            )}
          </div>
          <div>
            <label style={labelStyle}>Summary</label>
            <input
              type="text"
              placeholder="Brief summary of the issue"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              style={{
                ...inputStyle,
                borderColor: errors.title ? theme.colors.status.error : theme.colors.border,
              }}
            />
            {errors.title && (
              <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>
                {errors.title}
              </p>
            )}
          </div>
          <div>
            <label style={labelStyle}>Description (optional)</label>
            <textarea
              placeholder="Detailed description of what you observed"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              style={{ ...inputStyle, resize: "vertical" as const }}
            />
          </div>
          <div style={{ display: "flex", gap: theme.spacing.sm, justifyContent: "flex-end" }}>
            <button type="button" onClick={handleClose} style={getTabButtonStyle(theme, false)} disabled={submitting}>
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSubmit}
              disabled={submitting}
              style={{
                ...getTabButtonStyle(theme, true),
                background: theme.colors.primary,
                color: theme.colors.text.inverse,
              }}
            >
              {submitting ? "Submitting…" : "Submit report"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportErrorModal;
