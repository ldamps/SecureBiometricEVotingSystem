import React from "react";
import { useTheme } from "../../../styles/ThemeContext";
import { getLinkStyle } from "../../../features/voter/components/voterStyles";

interface VoterLinkProps extends React.AnchorHTMLAttributes<HTMLAnchorElement> {
  children: React.ReactNode;
  href: string;
}

const VoterLink: React.FC<VoterLinkProps> = ({ children, href, ...rest }) => {
  const { theme } = useTheme();
  const linkStyle = getLinkStyle(theme);
  return (
    <a href={href} style={linkStyle} {...rest}>
      {children}
    </a>
  );
};

export default VoterLink;
