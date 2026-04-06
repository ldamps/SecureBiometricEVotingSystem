import React, { useState } from "react";
import { useTheme } from "../../styles/ThemeContext";
import { useNavigate } from "react-router-dom";
import { getCardStyle, getTabButtonStyle, getStepFormInputStyle, getStepLabelStyle } from "../../styles/ui";
import { ApiClient } from "../../services/api-client.service";
import { ApiException } from "../../services/api-types";

interface ChangePasswordResponse {
  detail: string;
}

const OfficialOnboardingPage: React.FC = () => {
  const { theme } = useTheme();
  const { colors, spacing, fontSizes, fontWeights, borderRadius } = theme;
  const navigate = useNavigate();

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const validate = (): string | null => {
    if (!currentPassword) return "Please enter your temporary password.";
    if (!newPassword) return "Please enter a new password.";
    if (newPassword.length < 8) return "New password must be at least 8 characters.";
    if (newPassword === currentPassword) return "New password must be different from your temporary password.";
    if (newPassword !== confirmPassword) return "Passwords do not match.";
    return null;
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError(null);

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    setIsLoading(true);
    try {
      await ApiClient.post<ChangePasswordResponse>("/auth/change-password", {
        current_password: currentPassword,
        new_password: newPassword,
      });

      navigate("/official/home");
    } catch (err) {
      if (err instanceof ApiException) {
        setError(err.message || "Failed to change password.");
      } else {
        setError("Something went wrong. Please try again.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const card = getCardStyle(theme);

  const labelStyle = {
    ...getStepLabelStyle(theme),
    display: "block" as const,
    marginBottom: spacing.xs,
  };

  const inputStyle = {
    ...getStepFormInputStyle(theme),
    width: "100%",
    boxSizing: "border-box" as const,
  };

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        backgroundColor: colors.background,
        padding: spacing.xl,
      }}
    >
      <div style={{ ...card, maxWidth: 480, width: "100%" }}>
        <h1
          style={{
            marginTop: 0,
            marginBottom: spacing.sm,
            textAlign: "center",
            color: colors.text.primary,
            fontSize: fontSizes.xl,
          }}
        >
          Welcome to the Election Portal
        </h1>

        <p
          style={{
            textAlign: "center",
            color: colors.text.secondary,
            fontSize: fontSizes.sm,
            marginBottom: spacing.xl,
          }}
        >
          Your account has been created by an administrator. For security,
          please set a new password before continuing.
        </p>

        <form onSubmit={handleSubmit}>
          <div style={{ display: "flex", flexDirection: "column", gap: spacing.md }}>
            <div>
              <label htmlFor="current-password" style={labelStyle}>
                Temporary password
              </label>
              <input
                id="current-password"
                type="password"
                placeholder="The password from your welcome email"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                style={inputStyle}
                autoComplete="current-password"
              />
            </div>

            <div>
              <label htmlFor="new-password" style={labelStyle}>
                New password
              </label>
              <input
                id="new-password"
                type="password"
                placeholder="At least 8 characters"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                style={inputStyle}
                autoComplete="new-password"
              />
            </div>

            <div>
              <label htmlFor="confirm-password" style={labelStyle}>
                Confirm new password
              </label>
              <input
                id="confirm-password"
                type="password"
                placeholder="Re-enter your new password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                style={inputStyle}
                autoComplete="new-password"
              />
            </div>

            {error && (
              <p
                role="alert"
                style={{
                  margin: 0,
                  color: colors.status.error,
                  fontSize: fontSizes.sm,
                  textAlign: "center",
                }}
              >
                {error}
              </p>
            )}

            <button
              type="submit"
              disabled={isLoading}
              style={{
                ...getTabButtonStyle(theme, true),
                width: "100%",
                padding: `${spacing.md} ${spacing.lg}`,
                fontSize: fontSizes.base,
                fontWeight: fontWeights.medium,
                background: colors.primary,
                color: colors.text.inverse,
                cursor: isLoading ? "not-allowed" : "pointer",
                opacity: isLoading ? 0.75 : 1,
              }}
            >
              {isLoading ? "Setting password..." : "Set password and continue"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default OfficialOnboardingPage;
