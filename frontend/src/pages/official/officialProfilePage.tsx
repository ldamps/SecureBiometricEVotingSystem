// Official profile — signed-in election official (name + email).

import React, { useCallback, useEffect, useState } from "react";
import { useTheme } from "../../styles/ThemeContext";
import { OfficialApiRepository } from "../../features/officials/repositories/official-api.repository";
import { Official, OfficialRole } from "../../features/officials/model/official.model";
import {
  getCardStyle,
  getCardTitleStyle,
  getPageTitleStyle,
  getPageContentWrapperStyle,
  getCardTextStyle,
  getErrorAlertStyle,
} from "../../styles/ui";
import { getAccessTokenSubject } from "../../services/api-client.service";
import { ApiException } from "../../services/api-types";

const officialApiRepository = new OfficialApiRepository();

function displayName(o: Official): string {
  const first = o.first_name?.trim() ?? "";
  const last = o.last_name?.trim() ?? "";
  const combined = [first, last].filter(Boolean).join(" ");
  return combined || o.username;
}

function initials(o: Official): string {
  const first = o.first_name?.trim()?.[0];
  const last = o.last_name?.trim()?.[0];
  if (first && last) return `${first}${last}`.toUpperCase();
  if (first) return first.toUpperCase();
  const u = o.username?.trim() ?? "?";
  return u.slice(0, 2).toUpperCase();
}

function roleLabel(role: OfficialRole): string {
  return role === OfficialRole.ADMIN ? "Administrator" : "Election officer";
}

const OfficialProfilePage: React.FC = () => {
  const { theme } = useTheme();
  const { colors, spacing, fontSizes, fontWeights, borderRadius } = theme;

  const [official, setOfficial] = useState<Official | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadProfile = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    const officialId = getAccessTokenSubject();
    if (!officialId) {
      setError("No active session. Please sign in again.");
      setOfficial(null);
      setIsLoading(false);
      return;
    }
    try {
      const row = await officialApiRepository.getOfficial(officialId);
      setOfficial(row);
    } catch (err) {
      const message =
        err instanceof ApiException
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not load your profile.";
      setError(message);
      setOfficial(null);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void loadProfile();
  }, [loadProfile]);

  const pageWrapper = getPageContentWrapperStyle(theme);
  const pageTitle = getPageTitleStyle(theme);
  const card = getCardStyle(theme);
  const cardTitle = getCardTitleStyle(theme);
  const cardText = getCardTextStyle(theme);
  const errorAlert = getErrorAlertStyle(theme);

  const sectionPad = {
    paddingLeft: spacing.xl,
    paddingRight: spacing.xl,
    paddingBottom: spacing.lg,
  };

  const rowStyle: React.CSSProperties = {
    display: "flex",
    alignItems: "flex-start",
    gap: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.sm,
    borderBottom: `1px solid ${colors.border}`,
  };

  const labelStyle: React.CSSProperties = {
    ...cardText,
    flex: "0 0 140px",
    margin: 0,
    color: colors.text.secondary,
    fontSize: fontSizes.sm,
    fontWeight: fontWeights.medium,
  };

  const valueStyle: React.CSSProperties = {
    ...cardText,
    margin: 0,
    flex: 1,
    fontSize: fontSizes.base,
    color: colors.text.primary,
    wordBreak: "break-word" as const,
  };

  return (
    <div style={{ ...pageWrapper }}>
      <h1 style={{ ...pageTitle }}>Your profile</h1>

      <section style={sectionPad}>
        {isLoading && (
          <div style={{ ...card, padding: spacing.xl, textAlign: "center" }}>
            <p style={{ ...cardText, margin: 0, color: colors.text.secondary }}>
              Loading your details…
            </p>
          </div>
        )}

        {!isLoading && error && (
          <div style={errorAlert} role="alert">
            <p style={{ margin: 0, fontSize: fontSizes.sm }}>{error}</p>
          </div>
        )}

        {!isLoading && !error && official && (
          <div style={card}>
            <div
              style={{
                display: "flex",
                flexWrap: "wrap",
                alignItems: "center",
                gap: spacing.lg,
                marginBottom: spacing.lg,
              }}
            >
              <div
                style={{
                  width: 88,
                  height: 88,
                  borderRadius: "50%",
                  background: `linear-gradient(135deg, ${colors.primary} 0%, ${colors.primary}cc 100%)`,
                  color: colors.text.inverse,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontSize: fontSizes["2xl"],
                  fontWeight: fontWeights.bold,
                  flexShrink: 0,
                  boxShadow: colors.shadows?.md || "0 4px 14px rgba(0,0,0,0.12)",
                }}
                aria-hidden
              >
                {initials(official)}
              </div>
              <div style={{ flex: "1 1 200px", minWidth: 0 }}>
                <h2 style={{ ...cardTitle, marginTop: 0, marginBottom: spacing.xs, fontSize: fontSizes["2xl"] }}>
                  {displayName(official)}
                </h2>
                <p style={{ ...cardText, margin: 0, color: colors.text.secondary, fontSize: fontSizes.sm }}>
                  @{official.username}
                </p>
                <span
                  style={{
                    display: "inline-block",
                    marginTop: spacing.sm,
                    padding: `${spacing.xs} ${spacing.sm}`,
                    borderRadius: borderRadius?.md || "6px",
                    fontSize: fontSizes.xs,
                    fontWeight: fontWeights.semibold,
                    letterSpacing: "0.04em",
                    textTransform: "uppercase" as const,
                    backgroundColor:
                      official.role === OfficialRole.ADMIN
                        ? colors.status?.success + "22"
                        : colors.surfaceAlt,
                    color: colors.text.primary,
                    border: `1px solid ${colors.border}`,
                  }}
                >
                  {roleLabel(official.role)}
                </span>
              </div>
            </div>

            <h3
              style={{
                fontSize: fontSizes.lg,
                fontWeight: fontWeights.semibold,
                color: colors.text.primary,
                margin: `0 0 ${spacing.sm} 0`,
              }}
            >
              Contact
            </h3>

            <div style={{ ...rowStyle, borderTop: `1px solid ${colors.border}`, paddingTop: spacing.md }}>
              <p style={labelStyle}>Name</p>
              <p style={valueStyle}>{displayName(official)}</p>
            </div>
            <div style={{ ...rowStyle, borderBottom: "none", paddingBottom: 0 }}>
              <p style={labelStyle}>Email</p>
              <p style={valueStyle}>
                {official.email?.trim()
                  ? official.email
                  : <span style={{ color: colors.text.secondary, fontStyle: "italic" }}>Not on file</span>}
              </p>
            </div>
          </div>
        )}
      </section>
    </div>
  );
};

export default OfficialProfilePage;
