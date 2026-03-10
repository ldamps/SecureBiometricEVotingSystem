import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import { useState } from "react";
import { getPageContentWrapperStyle } from "../../styles/ui/section";
import { getPageTitleStyle } from "../../styles/ui/headers";
import { getTabsStyle } from "../../styles/ui/tabs";



const OfficialHomePage: React.FC = () => {
    const { theme } = useTheme();
    const tabs = ["overview", "investigations", "errors", "audit logs"];
    const [activeTab, setActiveTab] = useState("overview");

    
    return (
        <div style={{ ...getPageContentWrapperStyle(theme) }}>
            <h2 style={{ ...getPageTitleStyle(theme) }}>Investigation Dashboard</h2>

            </div>
    )
};

export default OfficialHomePage;
