import React, { useState, useEffect, useCallback } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import {
  getCardStyle,
  getCardTextStyle,
  getH3Style,
  getStepFormInputStyle,
  getStepLabelStyle,
  getTabButtonStyle,
  getTableStyle,
  getTableHeaderStyle,
  getTableCellStyle,
  getStatusBadgeStyle,
} from "../../../styles/ui";
import { Party, CreatePartyRequest } from "../model/candidate.model";
import { PartyApiRepository } from "../repositories/candidate-api.repository";

interface ManagePartiesProps {
  open: boolean;
  onClose: () => void;
}

interface FormState {
  party_name: string;
  abbreviation: string;
}

const BLANK_FORM: FormState = { party_name: "", abbreviation: "" };
const partyApi = new PartyApiRepository();

const ManageParties: React.FC<ManagePartiesProps> = ({ open, onClose }) => {
  const { theme } = useTheme();
  const [parties, setParties] = useState<Party[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(BLANK_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [showInactive, setShowInactive] = useState(false);

  const loadParties = useCallback(() => {
    setLoading(true);
    setError(null);
    partyApi.listParties()
      .then((all) => {
        if (showInactive) {
          partyApi.listDeletedParties()
            .then((deleted) => setParties([...all, ...deleted]))
            .catch(() => setParties(all));
        } else {
          setParties(all);
        }
      })
      .catch((err: Error) => setError(err.message || "Failed to load parties."))
      .finally(() => setLoading(false));
  }, [showInactive]);

  useEffect(() => {
    if (open) {
      loadParties();
      setForm(BLANK_FORM);
      setErrors({});
      setEditingId(null);
    }
  }, [open, loadParties]);

  if (!open) return null;

  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);
  const labelStyle = { ...getStepLabelStyle(theme), display: "block" as const, marginBottom: theme.spacing.xs };
  const inputStyle = { ...getStepFormInputStyle(theme), boxSizing: "border-box" as const };

  const validate = (): boolean => {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.party_name.trim()) next.party_name = "Required";
    setErrors(next);
    return Object.keys(next).length === 0;
  };

  const resetForm = () => {
    setForm(BLANK_FORM);
    setErrors({});
    setEditingId(null);
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!validate()) return;
    setSubmitting(true);
    setError(null);
    try {
      if (editingId) {
        await partyApi.updateParty(editingId, {
          party_name: form.party_name.trim(),
          abbreviation: form.abbreviation.trim() || undefined,
        });
      } else {
        const body: CreatePartyRequest = {
          party_name: form.party_name.trim(),
          abbreviation: form.abbreviation.trim() || undefined,
        };
        await partyApi.createParty(body);
      }
      resetForm();
      loadParties();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save party.");
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (p: Party) => {
    setEditingId(p.id);
    setForm({ party_name: p.party_name, abbreviation: p.abbreviation ?? "" });
    setErrors({});
  };

  const handleDelete = async (p: Party) => {
    if (!window.confirm(`Deactivate party "${p.party_name}"? Existing candidates remain linked.`)) return;
    setError(null);
    try {
      await partyApi.deleteParty(p.id);
      loadParties();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to deactivate party.");
    }
  };

  const handleRestore = async (p: Party) => {
    setError(null);
    try {
      await partyApi.restoreParty(p.id);
      loadParties();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to restore party.");
    }
  };

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="manage-parties-title"
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
      onClick={onClose}
    >
      <div
        style={{ ...card, width: "100%", maxWidth: 760, margin: theme.spacing.xl, maxHeight: "90vh", overflowY: "auto" }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="manage-parties-title" style={{ ...h3, marginBottom: theme.spacing.xs }}>Manage parties</h3>
        <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
          Parties are global. Candidates select a party when standing in an election.
        </p>

        {error && (
          <div style={{ padding: theme.spacing.sm, marginBottom: theme.spacing.md, background: theme.colors.status.error + "15", borderLeft: `4px solid ${theme.colors.status.error}`, borderRadius: theme.borderRadius.sm }}>
            <p style={{ margin: 0, color: theme.colors.status.error, fontSize: theme.fontSizes.sm }}>{error}</p>
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate style={{ marginBottom: theme.spacing.lg }}>
          <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr", gap: theme.spacing.md, marginBottom: theme.spacing.sm }}>
            <div>
              <label htmlFor="mp-name" style={labelStyle}>Party name</label>
              <input id="mp-name" type="text" value={form.party_name}
                onChange={(e) => setForm((p) => ({ ...p, party_name: e.target.value }))}
                style={{ ...inputStyle, borderColor: errors.party_name ? theme.colors.status.error : theme.colors.border }}
                autoComplete="off" />
              {errors.party_name && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.party_name}</p>}
            </div>
            <div>
              <label htmlFor="mp-abbr" style={labelStyle}>Abbreviation</label>
              <input id="mp-abbr" type="text" placeholder="e.g. LAB" value={form.abbreviation}
                onChange={(e) => setForm((p) => ({ ...p, abbreviation: e.target.value }))}
                style={inputStyle} autoComplete="off" />
            </div>
          </div>
          <div style={{ display: "flex", gap: theme.spacing.sm, justifyContent: "flex-end" }}>
            {editingId && (
              <button type="button" onClick={resetForm} disabled={submitting} style={getTabButtonStyle(theme, false)}>
                Cancel edit
              </button>
            )}
            <button type="submit" disabled={submitting}
              style={{ ...getTabButtonStyle(theme, true), background: theme.colors.primary, color: theme.colors.text.inverse, opacity: submitting ? 0.6 : 1 }}>
              {submitting ? "Saving..." : editingId ? "Save changes" : "+ Add party"}
            </button>
          </div>
        </form>

        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: theme.spacing.sm }}>
          <strong style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.primary }}>
            Parties ({parties.length})
          </strong>
          <label style={{ display: "flex", alignItems: "center", gap: theme.spacing.xs, fontSize: theme.fontSizes.xs, color: theme.colors.text.secondary, cursor: "pointer" }}>
            <input type="checkbox" checked={showInactive} onChange={(e) => setShowInactive(e.target.checked)} />
            Include deactivated
          </label>
        </div>

        {loading ? (
          <p style={{ ...cardText, color: theme.colors.text.secondary }}>Loading...</p>
        ) : parties.length === 0 ? (
          <p style={{ ...cardText, fontStyle: "italic" }}>No parties yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={getTableStyle(theme)}>
              <thead>
                <tr>
                  <th style={getTableHeaderStyle(theme)}>Name</th>
                  <th style={getTableHeaderStyle(theme)}>Abbreviation</th>
                  <th style={getTableHeaderStyle(theme)}>Status</th>
                  <th style={getTableHeaderStyle(theme)}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {parties.map((p) => (
                  <tr key={p.id}>
                    <td style={getTableCellStyle(theme)}>{p.party_name}</td>
                    <td style={getTableCellStyle(theme)}>{p.abbreviation ?? "—"}</td>
                    <td style={getTableCellStyle(theme)}>
                      <span style={getStatusBadgeStyle(theme, p.is_active ? "open" : "mismatch")}>
                        {p.is_active ? "ACTIVE" : "INACTIVE"}
                      </span>
                    </td>
                    <td style={{ ...getTableCellStyle(theme), whiteSpace: "nowrap" }}>
                      <div style={{ display: "flex", gap: theme.spacing.xs, flexWrap: "wrap" }}>
                        {p.is_active ? (
                          <>
                            <button type="button" onClick={() => startEdit(p)}
                              style={{ ...getTabButtonStyle(theme, true), background: theme.colors.primary, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                              Edit
                            </button>
                            <button type="button" onClick={() => handleDelete(p)}
                              style={{ ...getTabButtonStyle(theme, false), background: theme.colors.status.error, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                              Deactivate
                            </button>
                          </>
                        ) : (
                          <button type="button" onClick={() => handleRestore(p)}
                            style={{ ...getTabButtonStyle(theme, true), background: theme.colors.status.success, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                            Restore
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ display: "flex", justifyContent: "flex-end", marginTop: theme.spacing.lg }}>
          <button type="button" onClick={onClose} style={getTabButtonStyle(theme, false)}>
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManageParties;
