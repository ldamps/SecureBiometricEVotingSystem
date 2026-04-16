import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { getPageContentWrapperStyle, getPageTitleStyle } from "../../styles/ui";
import ManageOfficials from "../../features/officials/components/manageOfficials";

const ManageOfficialsPage: React.FC = () => {
  const { theme } = useTheme();

  return (
    <div style={getPageContentWrapperStyle(theme)}>
      <h1 style={getPageTitleStyle(theme)}>Manage Officials</h1>
      <div style={{ padding: theme.spacing.xl }}>
        <ManageOfficials />
      </div>
    </div>
  );
};

export default ManageOfficialsPage;
