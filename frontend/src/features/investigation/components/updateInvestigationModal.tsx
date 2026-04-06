import React, { useState, useEffect } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import {
  getCardStyle,
  getCardTextStyle,
  getH3Style,
  getStepFormInputStyle,
  getStepLabelStyle,
  getSelectStyle,
  getTabButtonStyle,
  getStatusBadgeStyle,
} from "../../../styles/ui";
import type { StatusBadgeVariant } from "../../../styles/ui";
import { InvestigationApiRepository } from "../repositories/investigation-api.repository";
import { Investigation, UpdateInvestigationRequest } from "../models/investigation.model";
import { Official } from "../../officials/model/official.model";
import { getAccessTokenSubject } from "../../../services/api-client.service";

const investigationApiRepository = new InvestigationApiRepository();

const STATUS_OPTIONS = ["OPEN", "IN_PROGRESS", "RESOLVED", "CLOSED"] as const;
const CATEGORY_OPTIONS = [
  "BALLOT_IRREGULARITY",
  "SYSTEM_ERROR",
  "VOTER_FRAUD",
  "TALLY_DISCREPANCY",
  "PROCESS_VIOLATION",
  "OTHER",
] as const;

const statusToBadge = (s: string): StatusBadgeVariant => {
  const lower = s.toLowerCase();
  if (lower === "resolved" || lower === "closed") return "resolved";
  if (lower === "in_progress") return "in_progress";
  return "open";
};

interface UpdateInvestigationModalProps {
  open: boolean;
  onClose: () => void;
  onUpdated?: () => void;
  investigation: Investigation | null;
  officials: Official[];
}

const UpdateInvestigationModal: React.FC<UpdateInvestigationModalProps> = ({
  open,
  onClose,
  onUpdated,
  investigation,
  officials,
}) => {
  const { theme } = useTheme();
  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);

  const [status, setStatus] = useState("");
  const [category, setCategory] = useState("");
  const [assignedTo, setAssignedTo] = useState("");
  const [notes, setNotes] = useState("");
  const [resolutionSummary, setResolutionSummary] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (investigation && open) {
      setStatus(investigation.status);
      setCategory(investigation.category || "");
      setAssignedTo(investigation.assigned_to || "");
      setNotes(investigation.notes || "");
      setResolutionSummary(investigation.resolution_summary || "");
      setSubmitError(null);
      setErrors({});
    }
  }, [investigation, open]);

  if (!open || !investigation) return null;

  const isResolving = status === "RESOLVED" || status === "CLOSED";

  const validate = (): boolean => {
    const next: Record<string, string> = {};
    if (isResolving && !resolutionSummary.trim()) {
      next.resolutionSummary =
        "A resolution summary is required when resolving or closing an investigation.";
    }
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    setSubmitting(true);
    setSubmitError(null);

    const body: UpdateInvestigationRequest = {};

    if (status !== investigation.status) body.status = status;
    if (category !== (investigation.category || "")) body.category = category || undefined;
    if (assignedTo !== (investigation.assigned_to || "")) body.assigned_to = assignedTo || undefined;
    if (notes !== (investigation.notes || "")) body.notes = notes || undefined;
    if (resolutionSummary !== (investigation.resolution_summary || ""))
      body.resolution_summary = resolutionSummary || undefined;

    if (isResolving) {
      const officialId = getAccessTokenSubject();
      if (officialId) body.resolved_by = officialId;
    }

    if (Object.keys(body).length === 0) {
      handleClose();
      return;
    }

    await investigationApiRepository
      .updateInvestigation(investigation.id, body)
      .then(() => {
        onUpdated?.();
        onClose();
      })
      .catch((err: Error) => {
        setSubmitError(err.message || "Failed to update investigation.");
      })
      .finally(() => setSubmitting(false));
  };

  const handleClose = () => {
    setSubmitError(null);
    setErrors({});
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

  const formatDateTime = (iso: string): string => {
    if (!iso) return "\u2014";
    const d = new Date(iso);
    if (isNaN(d.getTime())) return iso;
    return d.toLocaleString("en-GB", { dateStyle: "medium", timeStyle: "short" });
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="update-investigation-title"
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
          maxWidth: 560,
          margin: theme.spacing.xl,
          maxHeight: "90vh",
          overflow: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="update-investigation-title" style={h3}>
          Manage investigation
        </h3>

        {/* Investigation context */}
        <div
          style={{
            ...cardText,
            marginBottom: theme.spacing.md,
            padding: theme.spacing.md,
            background: theme.colors.surfaceAlt,
            borderRadius: theme.borderRadius.md,
          }}
        >
          <p style={{ margin: 0, fontWeight: theme.fontWeights.medium }}>
            {investigation.title}
          </p>
          <p
            style={{
              margin: `${theme.spacing.xs} 0 0`,
              fontSize: theme.fontSizes.sm,
              color: theme.colors.text.secondary,
            }}
          >
            Severity: {investigation.severity} · Raised{" "}
            {formatDateTime(investigation.raised_at)}
          </p>
          {investigation.description && (
            <p
              style={{
                margin: `${theme.spacing.sm} 0 0`,
                fontSize: theme.fontSizes.sm,
              }}
            >
              {investigation.description}
            </p>
          )}
        </div>

        {submitError && (
          <p
            style={{
              ...cardText,
              color: theme.colors.status.error,
              marginBottom: theme.spacing.md,
            }}
          >
            {submitError}
          </p>
        )}

        <div
          style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}
        >
          {/* Status */}
          <div>
            <label style={labelStyle}>Status</label>
            <div style={{ display: "flex", alignItems: "center", gap: theme.spacing.sm }}>
              <select
                value={status}
                onChange={(e) => setStatus(e.target.value)}
                style={{
                  ...getSelectStyle(theme),
                  flex: 1,
                  boxSizing: "border-box",
                }}
              >
                {STATUS_OPTIONS.map((s) => (
                  <option key={s} value={s}>
                    {s.replace(/_/g, " ")}
                  </option>
                ))}
              </select>
              <span style={getStatusBadgeStyle(theme, statusToBadge(status))}>
                {status.replace(/_/g, " ")}
              </span>
            </div>
          </div>

          {/* Category */}
          <div>
            <label style={labelStyle}>Category</label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              style={{
                ...getSelectStyle(theme),
                width: "100%",
                boxSizing: "border-box",
              }}
            >
              <option value="">— Uncategorised —</option>
              {CATEGORY_OPTIONS.map((c) => (
                <option key={c} value={c}>
                  {c.replace(/_/g, " ")}
                </option>
              ))}
            </select>
          </div>

          {/* Assign to */}
          <div>
            <label style={labelStyle}>Assign to official</label>
            <select
              value={assignedTo}
              onChange={(e) => setAssignedTo(e.target.value)}
              style={{
                ...getSelectStyle(theme),
                width: "100%",
                boxSizing: "border-box",
              }}
            >
              <option value="">— Unassigned —</option>
              {officials.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.first_name} {o.last_name} ({o.username})
                </option>
              ))}
            </select>
          </div>

          {/* Notes */}
          <div>
            <label style={labelStyle}>Internal notes</label>
            <textarea
              placeholder="Add investigation notes, findings, or next steps"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={3}
              style={{ ...inputStyle, resize: "vertical" as const }}
            />
          </div>

          {/* Resolution summary — shown when resolving/closing */}
          {isResolving && (
            <div>
              <label style={labelStyle}>
                Resolution summary{" "}
                <span style={{ color: theme.colors.status.error }}>*</span>
              </label>
              <p
                style={{
                  ...cardText,
                  fontSize: theme.fontSizes.xs,
                  color: theme.colors.text.secondary,
                  margin: `0 0 ${theme.spacing.xs}`,
                }}
              >
                Describe the findings and any actions taken. This is required for
                audit and accountability.
              </p>
              <textarea
                placeholder="e.g. Investigated tally discrepancy in constituency X. Root cause: duplicate ballot token issuance. Corrective action: voided duplicate tokens, recount confirmed original totals are accurate."
                value={resolutionSummary}
                onChange={(e) => setResolutionSummary(e.target.value)}
                rows={4}
                style={{
                  ...inputStyle,
                  resize: "vertical" as const,
                  borderColor: errors.resolutionSummary
                    ? theme.colors.status.error
                    : theme.colors.border,
                }}
              />
              {errors.resolutionSummary && (
                <p
                  style={{
                    margin: `${theme.spacing.xs} 0 0`,
                    fontSize: theme.fontSizes.xs,
                    color: theme.colors.status.error,
                  }}
                >
                  {errors.resolutionSummary}
                </p>
              )}
            </div>
          )}

          {/* Actions */}
          <div
            style={{
              display: "flex",
              gap: theme.spacing.sm,
              justifyContent: "flex-end",
            }}
          >
            <button
              type="button"
              onClick={handleClose}
              style={getTabButtonStyle(theme, false)}
              disabled={submitting}
            >
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
              {submitting ? "Saving\u2026" : "Save changes"}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default UpdateInvestigationModal;
