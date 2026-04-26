import React, { useState, useEffect, useCallback } from "react";
import { useTheme } from "../../../styles/ThemeContext";
import {
  getCardStyle,
  getCardTextStyle,
  getH3Style,
  getStepFormInputStyle,
  getStepLabelStyle,
  getTabButtonStyle,
  getSelectStyle,
  getTableStyle,
  getTableHeaderStyle,
  getTableCellStyle,
  getStatusBadgeStyle,
} from "../../../styles/ui";
import {
  Candidate,
  CreateCandidateRequest,
  Party,
} from "../model/candidate.model";
import { Election } from "../model/election.model";
import { Constituency } from "../model/constituency.model";
import {
  CandidateApiRepository,
  PartyApiRepository,
} from "../repositories/candidate-api.repository";
import { ConstituencyApiRepository } from "../repositories/constituency-api.repository";

interface ManageCandidatesProps {
  open: boolean;
  election: Election | null;
  onClose: () => void;
}

interface FormState {
  first_name: string;
  last_name: string;
  party_id: string;
  constituency_id: string;
}

const BLANK_FORM: FormState = {
  first_name: "",
  last_name: "",
  party_id: "",
  constituency_id: "",
};

const candidateApi = new CandidateApiRepository();
const partyApi = new PartyApiRepository();
const constituencyApi = new ConstituencyApiRepository();

const ManageCandidates: React.FC<ManageCandidatesProps> = ({ open, election, onClose }) => {
  const { theme } = useTheme();
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [parties, setParties] = useState<Party[]>([]);
  const [constituencies, setConstituencies] = useState<Constituency[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [form, setForm] = useState<FormState>(BLANK_FORM);
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);

  const loadData = useCallback(() => {
    if (!election) return;
    setLoading(true);
    setError(null);
    Promise.all([
      candidateApi.listCandidates(election.id),
      partyApi.listParties(),
      constituencyApi.listConstituencies(),
    ])
      .then(([cands, pts, cons]) => {
        setCandidates(cands);
        setParties(pts.filter((p) => p.is_active));
        setConstituencies(cons);
      })
      .catch((err: Error) => setError(err.message || "Failed to load data."))
      .finally(() => setLoading(false));
  }, [election]);

  useEffect(() => {
    if (open && election) {
      loadData();
      setForm(BLANK_FORM);
      setErrors({});
      setEditingId(null);
    }
  }, [open, election, loadData]);

  if (!open || !election) return null;

  const card = getCardStyle(theme);
  const cardText = getCardTextStyle(theme);
  const h3 = getH3Style(theme);
  const labelStyle = { ...getStepLabelStyle(theme), display: "block" as const, marginBottom: theme.spacing.xs };
  const inputStyle = { ...getStepFormInputStyle(theme), boxSizing: "border-box" as const };

  const partyMap = new Map(parties.map((p) => [p.id, p]));
  const constituencyMap = new Map(constituencies.map((c) => [c.id, c]));
  const electionConstituencies = constituencies.filter((c) =>
    election.constituency_ids.includes(c.id),
  );

  const validate = (): boolean => {
    const next: Partial<Record<keyof FormState, string>> = {};
    if (!form.first_name.trim()) next.first_name = "Required";
    if (!form.last_name.trim()) next.last_name = "Required";
    if (!editingId) {
      if (!form.party_id) next.party_id = "Required";
      if (!form.constituency_id) next.constituency_id = "Required";
    }
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
        await candidateApi.updateCandidate(election.id, editingId, {
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim(),
        });
      } else {
        const body: CreateCandidateRequest = {
          first_name: form.first_name.trim(),
          last_name: form.last_name.trim(),
          party_id: form.party_id,
          constituency_id: form.constituency_id,
        };
        await candidateApi.createCandidate(election.id, body);
      }
      resetForm();
      loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to save candidate.");
    } finally {
      setSubmitting(false);
    }
  };

  const startEdit = (c: Candidate) => {
    setEditingId(c.id);
    setForm({
      first_name: c.first_name,
      last_name: c.last_name,
      party_id: c.party_id,
      constituency_id: c.constituency_id,
    });
    setErrors({});
  };

  const handleToggleActive = async (c: Candidate) => {
    setError(null);
    try {
      await candidateApi.updateCandidate(election.id, c.id, {
        is_active: !c.is_active,
      });
      loadData();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update candidate.");
    }
  };

  const electionLocked = election.status !== "DRAFT";
  const noConstituencies = electionConstituencies.length === 0;
  const noParties = parties.length === 0;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="manage-candidates-title"
      style={{ position: "fixed", inset: 0, background: "rgba(0,0,0,0.4)", display: "flex", alignItems: "center", justifyContent: "center", zIndex: 1000 }}
      onClick={onClose}
    >
      <div
        style={{ ...card, width: "100%", maxWidth: 860, margin: theme.spacing.xl, maxHeight: "90vh", overflowY: "auto" }}
        onClick={(e) => e.stopPropagation()}
      >
        <h3 id="manage-candidates-title" style={{ ...h3, marginBottom: theme.spacing.xs }}>
          Manage candidates — {election.title}
        </h3>
        <p style={{ ...cardText, marginBottom: theme.spacing.lg }}>
          One candidate per party per constituency is allowed.
        </p>

        {error && (
          <div style={{ padding: theme.spacing.sm, marginBottom: theme.spacing.md, background: theme.colors.status.error + "15", borderLeft: `4px solid ${theme.colors.status.error}`, borderRadius: theme.borderRadius.sm }}>
            <p style={{ margin: 0, color: theme.colors.status.error, fontSize: theme.fontSizes.sm }}>{error}</p>
          </div>
        )}

        {electionLocked && (
          <div style={{ padding: theme.spacing.sm, marginBottom: theme.spacing.md, background: theme.colors.status.warning + "15", borderLeft: `4px solid ${theme.colors.status.warning}`, borderRadius: theme.borderRadius.sm }}>
            <p style={{ margin: 0, color: theme.colors.text.primary, fontSize: theme.fontSizes.sm }}>
              This election is {election.status}. New candidates can only be added while the election is in DRAFT status.
            </p>
          </div>
        )}

        {!electionLocked && (noConstituencies || noParties) && (
          <div style={{ padding: theme.spacing.sm, marginBottom: theme.spacing.md, background: theme.colors.status.warning + "15", borderLeft: `4px solid ${theme.colors.status.warning}`, borderRadius: theme.borderRadius.sm }}>
            <p style={{ margin: 0, color: theme.colors.text.primary, fontSize: theme.fontSizes.sm }}>
              {noConstituencies && "Add at least one constituency to this election before adding candidates. "}
              {noParties && "Create at least one party before adding candidates."}
            </p>
          </div>
        )}

        {!electionLocked && !noConstituencies && !noParties && (
          <form onSubmit={handleSubmit} noValidate style={{ marginBottom: theme.spacing.lg }}>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: theme.spacing.md, marginBottom: theme.spacing.sm }}>
              <div>
                <label htmlFor="mc-first" style={labelStyle}>First name</label>
                <input id="mc-first" type="text" value={form.first_name}
                  onChange={(e) => setForm((p) => ({ ...p, first_name: e.target.value }))}
                  style={{ ...inputStyle, borderColor: errors.first_name ? theme.colors.status.error : theme.colors.border }}
                  autoComplete="off" />
                {errors.first_name && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.first_name}</p>}
              </div>
              <div>
                <label htmlFor="mc-last" style={labelStyle}>Last name</label>
                <input id="mc-last" type="text" value={form.last_name}
                  onChange={(e) => setForm((p) => ({ ...p, last_name: e.target.value }))}
                  style={{ ...inputStyle, borderColor: errors.last_name ? theme.colors.status.error : theme.colors.border }}
                  autoComplete="off" />
                {errors.last_name && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.last_name}</p>}
              </div>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: theme.spacing.md, marginBottom: theme.spacing.sm }}>
              <div>
                <label htmlFor="mc-party" style={labelStyle}>Party</label>
                <select id="mc-party" value={form.party_id}
                  disabled={editingId !== null}
                  onChange={(e) => setForm((p) => ({ ...p, party_id: e.target.value }))}
                  style={{ ...getSelectStyle(theme), width: "100%", boxSizing: "border-box", borderColor: errors.party_id ? theme.colors.status.error : theme.colors.border }}>
                  <option value="">-- Select party --</option>
                  {parties.map((p) => (
                    <option key={p.id} value={p.id}>
                      {p.party_name}{p.abbreviation ? ` (${p.abbreviation})` : ""}
                    </option>
                  ))}
                </select>
                {errors.party_id && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.party_id}</p>}
              </div>
              <div>
                <label htmlFor="mc-cons" style={labelStyle}>Constituency</label>
                <select id="mc-cons" value={form.constituency_id}
                  disabled={editingId !== null}
                  onChange={(e) => setForm((p) => ({ ...p, constituency_id: e.target.value }))}
                  style={{ ...getSelectStyle(theme), width: "100%", boxSizing: "border-box", borderColor: errors.constituency_id ? theme.colors.status.error : theme.colors.border }}>
                  <option value="">-- Select constituency --</option>
                  {electionConstituencies.map((c) => (
                    <option key={c.id} value={c.id}>{c.name} ({c.country})</option>
                  ))}
                </select>
                {errors.constituency_id && <p style={{ margin: `${theme.spacing.xs} 0 0`, fontSize: theme.fontSizes.xs, color: theme.colors.status.error }}>{errors.constituency_id}</p>}
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
                {submitting ? "Saving..." : editingId ? "Save changes" : "+ Add candidate"}
              </button>
            </div>
          </form>
        )}

        <strong style={{ fontSize: theme.fontSizes.sm, color: theme.colors.text.primary, display: "block", marginBottom: theme.spacing.sm }}>
          Candidates ({candidates.length})
        </strong>

        {loading ? (
          <p style={{ ...cardText, color: theme.colors.text.secondary }}>Loading...</p>
        ) : candidates.length === 0 ? (
          <p style={{ ...cardText, fontStyle: "italic" }}>No candidates added yet.</p>
        ) : (
          <div style={{ overflowX: "auto" }}>
            <table style={getTableStyle(theme)}>
              <thead>
                <tr>
                  <th style={getTableHeaderStyle(theme)}>Name</th>
                  <th style={getTableHeaderStyle(theme)}>Party</th>
                  <th style={getTableHeaderStyle(theme)}>Constituency</th>
                  <th style={getTableHeaderStyle(theme)}>Status</th>
                  <th style={getTableHeaderStyle(theme)}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {candidates.map((c) => {
                  const party = partyMap.get(c.party_id);
                  const cons = constituencyMap.get(c.constituency_id);
                  return (
                    <tr key={c.id}>
                      <td style={getTableCellStyle(theme)}>{c.first_name} {c.last_name}</td>
                      <td style={getTableCellStyle(theme)}>
                        {party ? party.party_name : c.party_id.slice(0, 8)}
                      </td>
                      <td style={getTableCellStyle(theme)}>
                        {cons ? cons.name : c.constituency_id.slice(0, 8)}
                      </td>
                      <td style={getTableCellStyle(theme)}>
                        <span style={getStatusBadgeStyle(theme, c.is_active ? "open" : "mismatch")}>
                          {c.is_active ? "ACTIVE" : "INACTIVE"}
                        </span>
                      </td>
                      <td style={{ ...getTableCellStyle(theme), whiteSpace: "nowrap" }}>
                        <div style={{ display: "flex", gap: theme.spacing.xs, flexWrap: "wrap" }}>
                          {!electionLocked && (
                            <button type="button" onClick={() => startEdit(c)}
                              style={{ ...getTabButtonStyle(theme, true), background: theme.colors.primary, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                              Edit
                            </button>
                          )}
                          <button type="button" onClick={() => handleToggleActive(c)}
                            style={{ ...getTabButtonStyle(theme, false), background: c.is_active ? theme.colors.status.error : theme.colors.status.success, color: theme.colors.text.inverse, padding: `${theme.spacing.xs} ${theme.spacing.sm}`, fontSize: theme.fontSizes.xs }}>
                            {c.is_active ? "Deactivate" : "Activate"}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
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

export default ManageCandidates;
