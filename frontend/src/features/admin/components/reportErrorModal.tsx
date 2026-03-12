import React from "react";
import { useTheme } from "../../../styles/ThemeContext";
import { getCardStyle, getCardTextStyle, getH3Style } from "../../../styles/ui";
import type { Theme } from "../../../styles/theme";

const getSelectStyle = (theme: Theme) => ({
  padding: `${theme.spacing.sm} ${theme.spacing.md}`,
  borderRadius: theme.borderRadius.md,
  border: `1px solid ${theme.colors.border}`,
  background: theme.colors.surface,
  color: theme.colors.text.primary,
  fontSize: theme.fontSizes.base,
  minWidth: "280px",
});

const getTabButtonStyle = (theme: Theme, active: boolean) => ({
  padding: `${theme.spacing.sm} ${theme.spacing.md}`,
  border: "none",
  borderRadius: theme.borderRadius.md,
  background: active ? theme.colors.primary : "transparent",
  color: active ? theme.colors.text.inverse : theme.colors.text.primary,
  fontWeight: theme.fontWeights.medium,
  cursor: "pointer",
  fontSize: theme.fontSizes.base,
});

interface ReportErrorModalProps {
  open: boolean;
  onClose: () => void;
  context?: string | null;
}

const ReportErrorModal: React.FC<ReportErrorModalProps> = ({ open, onClose, context = null }) => {
  const { theme } = useTheme();
  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);

  if (!open) return null;

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
      onClick={onClose}
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
          Report discrepancies or issues when you see them. (Form submission not implemented.)
        </p>
        <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
          <div>
            <label
              style={{
                display: "block",
                marginBottom: theme.spacing.xs,
                fontSize: theme.fontSizes.sm,
                color: theme.colors.text.secondary,
              }}
            >
              Category
            </label>
            <select style={getSelectStyle(theme)} disabled>
              <option>— Select category —</option>
            </select>
          </div>
          <div>
            <label
              style={{
                display: "block",
                marginBottom: theme.spacing.xs,
                fontSize: theme.fontSizes.sm,
                color: theme.colors.text.secondary,
              }}
            >
              Summary
            </label>
            <input
              type="text"
              placeholder="Brief summary"
              disabled
              style={{ ...getSelectStyle(theme), width: "100%" }}
            />
          </div>
          <div>
            <label
              style={{
                display: "block",
                marginBottom: theme.spacing.xs,
                fontSize: theme.fontSizes.sm,
                color: theme.colors.text.secondary,
              }}
            >
              Description
            </label>
            <textarea
              placeholder="Details"
              disabled
              rows={3}
              style={{ ...getSelectStyle(theme), width: "100%", resize: "vertical" }}
            />
          </div>
          <div style={{ display: "flex", gap: theme.spacing.sm, justifyContent: "flex-end" }}>
            <button type="button" onClick={onClose} style={getTabButtonStyle(theme, false)}>
              Cancel
            </button>
            <button type="button" disabled style={getTabButtonStyle(theme, true)}>
              Submit (not implemented)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ReportErrorModal;
