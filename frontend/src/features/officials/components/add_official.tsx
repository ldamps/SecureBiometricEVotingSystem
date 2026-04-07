import React, { useState } from "react";
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
import { OfficialRole } from "../model/official.model";

export interface NewOfficialData {
  firstName: string;
  lastName: string;
  email: string;
  role: string;
}

interface AddOfficialProps {
  open: boolean;
  onClose: () => void;
  onAdd: (data: NewOfficialData) => void;
}

const BLANK_FORM: NewOfficialData = {
  firstName: "",
  lastName: "",
  email: "",
  role: "",
};

const ROLE_OPTIONS: { value: OfficialRole; label: string }[] = [
  { value: OfficialRole.OFFICER, label: "Election Officer" },
  { value: OfficialRole.ADMIN, label: "Administrator" },
];

const AddOfficial: React.FC<AddOfficialProps> = ({ open, onClose, onAdd }) => {
  const { theme } = useTheme();
  const [form, setForm] = useState<NewOfficialData>(BLANK_FORM);
  const [errors, setErrors] = useState<Partial<NewOfficialData>>({});

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

  const validate = (): boolean => {
    const next: Partial<NewOfficialData> = {};
    if (!form.firstName.trim()) next.firstName = "Required";
    if (!form.lastName.trim()) next.lastName = "Required";
    if (!form.email.trim()) {
      next.email = "Required";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
      next.email = "Enter a valid email address";
    }
    if (!form.role) next.role = "Required";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validate()) return;
    onAdd(form);
    setForm(BLANK_FORM);
    setErrors({});
  };

  const handleClose = () => {
    setForm(BLANK_FORM);
    setErrors({});
    onClose();
  };

  const field = (
    id: keyof NewOfficialData,
    label: string,
    type: string = "text",
    placeholder: string = ""
  ) => (
    <div>
      <label htmlFor={`add-official-${id}`} style={labelStyle}>
        {label}
      </label>
      <input
        id={`add-official-${id}`}
        type={type}
        placeholder={placeholder}
        value={form[id]}
        onChange={(e) => setForm((prev) => ({ ...prev, [id]: e.target.value }))}
        style={{
          ...inputStyle,
          borderColor: errors[id] ? theme.colors.status.error : theme.colors.border,
        }}
        autoComplete="off"
      />
      {errors[id] && (
        <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>
          {errors[id]}
        </p>
      )}
    </div>
  );

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="add-official-title"
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
          maxWidth: 520,
          margin: theme.spacing.xl,
          maxHeight: "90vh",
          overflowY: "auto",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="add-official-title" style={{ ...h3, marginBottom: theme.spacing.xs }}>
          Add election official
        </h3>
        <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
          Set up the official's profile. They will receive an invitation to complete their biometric setup.
        </p>

        <form onSubmit={handleSubmit} noValidate>
          <div style={{ display: "flex", flexDirection: "column", gap: theme.spacing.md }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: theme.spacing.md }}>
              {field("firstName", "First name", "text", "e.g. Jane")}
              {field("lastName", "Last name", "text", "e.g. Smith")}
            </div>

            {field("email", "Email address", "email", "e.g. jane.smith@gov.uk")}

            <div>
              <label htmlFor="add-official-role" style={labelStyle}>
                Role
              </label>
              <select
                id="add-official-role"
                value={form.role}
                onChange={(e) => setForm((prev) => ({ ...prev, role: e.target.value }))}
                style={{
                  ...getSelectStyle(theme),
                  width: "100%",
                  boxSizing: "border-box",
                  borderColor: errors.role ? theme.colors.status.error : theme.colors.border,
                }}
              >
                <option value="">— Select role —</option>
                {ROLE_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
              {errors.role && (
                <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>
                  {errors.role}
                </p>
              )}
            </div>

            <div style={{ display: "flex", gap: theme.spacing.sm, justifyContent: "flex-end", paddingTop: theme.spacing.sm }}>
              <button type="button" onClick={handleClose} style={getTabButtonStyle(theme, false)}>
                Cancel
              </button>
              <button
                type="submit"
                style={{
                  ...getTabButtonStyle(theme, true),
                  background: theme.colors.primary,
                  color: theme.colors.text.inverse,
                }}
              >
                Add official
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddOfficial;
