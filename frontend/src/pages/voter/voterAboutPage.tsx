import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import {
  getH3Style,
  getPAfterHeaderStyle,
  getFirstSectionStyle,
  getSectionH2Style,
  getSectionWithPaddingStyle,
  getListStyle,
  getLinkStyle,
  getSectionIconStyle,
  getPageTitleStyle,
  getVoterPageContentWrapperStyle,
} from "../../styles/ui";

const VoterAboutPage: React.FC = () => {
  const { theme } = useTheme();
  const h3Style = getH3Style(theme);
  const pAfterHeaderStyle = getPAfterHeaderStyle(theme);
  const firstSectionStyle = getFirstSectionStyle(theme);
  const sectionH2Style = getSectionH2Style(theme);
  const sectionWithPaddingStyle = getSectionWithPaddingStyle(theme);
  const listStyle = getListStyle(theme);
  const linkStyle = getLinkStyle(theme);
  const sectionIconStyle = getSectionIconStyle(theme);
  const pageTitleStyle = getPageTitleStyle(theme);
  const wrapperStyle = getVoterPageContentWrapperStyle(theme);

  const sectionDiamond = (
    <svg width="0.65em" height="0.65em" viewBox="0 0 24 24" style={sectionIconStyle} aria-hidden>
      <rect x="4" y="4" width="16" height="16" rx="2" transform="rotate(45 12 12)" />
    </svg>
  );

  return (
    <div>
      <style>{`
        .voter-about-page a:hover { color: ${theme.colors.primaryHover}; }
      `}</style>
      <div className="voter-about-page">
        <div className="voter-about-page voter-page-content" style={wrapperStyle}>
          <header>
            <h1 style={pageTitleStyle}>About the Platform</h1>
          </header>

          {/* About the platform */}
          <section style={firstSectionStyle}>
            <p>
              The Official UK Voting Platform is a secure, accessible and legally compliant e-voting system that enables eligible voters across the United Kingdom to register, manage their electoral details and cast their vote from their own trusted devices. Our purpose is to modernise participation in democratic processes while upholding the highest standards of integrity, confidentiality and public trust.
              <br />
              <br />
              The platform supports a range of UK election types, including General Elections, Local Elections, Mayoral Elections, Scottish Parliament and London Assembly Elections, as well as public referendums. Multiple voting systems are supported, including First Past the Post (FPTP), Additional Member System (AMS), Single Transferable Vote (STV) and the Alternative Vote, ensuring the platform can serve the full spectrum of UK democratic processes.
            </p>
          </section>

          {/* How We Protect Your Vote */}
          <section style={sectionWithPaddingStyle}>
            <h2 style={sectionH2Style}>How We Protect Your Vote</h2>

            {/* Biometric Identity Verification */}
            <h3 style={h3Style}>{sectionDiamond}Biometric Identity Verification</h3>
            <p style={pAfterHeaderStyle}>
              To prevent electoral fraud, the platform uses multi-modal biometric verification combining both facial and ear recognition. Before you can cast a vote, your identity is confirmed through a secure challenge-response process:
              <ul style={listStyle}>
                <li>During registration, your device generates a cryptographic key pair that is encrypted using your biometric data</li>
                <li>Your raw biometric templates are never sent to or stored on our servers</li>
                <li>When you vote, the server issues a cryptographic challenge that can only be signed by unlocking your private key with a successful biometric match on your device</li>
                <li>Both facial and ear biometrics must independently pass verification for authentication to succeed</li>
              </ul>
              This match-on-device architecture means that your biometric data remains under your control at all times, stored only on the device you registered with.
            </p>

            {/* Vote Anonymity and Ballot Tokens */}
            <h3 style={h3Style}>{sectionDiamond}Vote Anonymity and Ballot Tokens</h3>
            <p style={pAfterHeaderStyle}>
              Once your identity has been verified, you are issued a one-time ballot token. This token is used to submit your vote, and it is designed so that your vote cannot be linked back to your identity:
              <ul style={listStyle}>
                <li>Ballot tokens are cryptographically hashed to prevent tracing</li>
                <li>Your vote record contains no voter identification — only your ballot selection and the anonymous token</li>
                <li>A separate voter ledger records that you have participated in the election, preventing double voting without revealing how you voted</li>
                <li>Each token can only be used once and is marked as used upon vote submission</li>
              </ul>
            </p>

            {/* Encryption and Data Security */}
            <h3 style={h3Style}>{sectionDiamond}Encryption and Data Security</h3>
            <p style={pAfterHeaderStyle}>
              All sensitive data held by the platform is protected by encryption both in transit and at rest. Communications between your device and our servers are secured with TLS. Stored data, including personal details and ballot tokens, is encrypted using managed encryption keys with strict access controls. Role-based access ensures that only authorised personnel can access specific data, and all access is logged for audit purposes.
            </p>
          </section>

          {/* Commitment to Data Protection in the UK */}
          <section style={sectionWithPaddingStyle}>
            <h2 style={sectionH2Style}>Our Commitment to Data Protection in the UK</h2>
            <p style={pAfterHeaderStyle}>
              The protection of personal data is central to our operations. We process information strictly in accordance with the UK General Data Protection Regulation (UK GDPR) and the Data Protection Act 2018. Our practices are guided by regulatory expectations set out by the Information Commissioner's Office (ICO).
              <br />
              We adhere to the core principles of UK data protection law:
              <ul style={listStyle}>
                <li><strong>Lawfulness, fairness and transparency:</strong> Personal data is processed only where a clear lawful basis applies</li>
                <li><strong>Purpose limitation:</strong> Information is collected for specific, legitimate and lawful purposes only</li>
                <li><strong>Data minimisation:</strong> Only the minimum amount of data necessary is collected and processed</li>
                <li><strong>Accuracy:</strong> Data is kept up to date and accurate</li>
                <li><strong>Storage limitation:</strong> Data is stored for no longer than necessary</li>
                <li><strong>Integrity and confidentiality:</strong> Data is protected against unauthorised access and disclosure</li>
              </ul>
            </p>

            {/* Privacy by Design */}
            <h3 style={h3Style}>{sectionDiamond}Privacy by Design</h3>
            <p style={pAfterHeaderStyle}>
              Data protection is embedded into our platform architecture. Through privacy-by-design and privacy-by-default practices, we ensure that:
              <ul style={listStyle}>
                <li><strong>Only essential data is collected and processed</strong></li>
                <li><strong>Access to data is strictly role-based and access controls are enforced</strong></li>
                <li><strong>Encryption protects sensitive data in transit and at rest</strong></li>
                <li><strong>Biometric verification uses a match-on-device model — raw biometric data never leaves your device</strong></li>
                <li><strong>Continuous monitoring and audit trails are in place</strong></li>
              </ul>
              Where processing activities present high risks to individual rights and freedoms, we conduct Data Protection Impact Assessments (DPIAs) in accordance with UK GDPR requirements.
            </p>

            {/* Transparency and Individual Rights */}
            <h3 style={h3Style}>{sectionDiamond}Transparency and Individual Rights</h3>
            <p style={pAfterHeaderStyle}>
              The Official UK Voting Platform is committed to openness about how personal data is used. Clear privacy notices explain:
              <ul style={listStyle}>
                <li>What data is collected</li>
                <li>Why it is collected</li>
                <li>How long it is retained</li>
                <li>How it is protected</li>
              </ul>
              Individual rights are fully upheld under UK GDPR, including the right of access, rectification, restriction, objection and where applicable, erasure. Procedures are in place to respond to requests within statutory timeframes.
              <br />
              <br />
              In the unlikely event of a personal data breach, we follow established incident response procedures and where legally required, notify the Information Commissioner's Office within the mandated timeframe.
            </p>

            {/* Accountability and Governance */}
            <h3 style={h3Style}>{sectionDiamond}Accountability and Governance</h3>
            <p style={pAfterHeaderStyle}>
              We maintain robust governance frameworks to ensure compliance, including:
              <ul style={listStyle}>
                <li>Documented records of data processing activities</li>
                <li>Internal audit and compliance procedures</li>
              </ul>
              Where required, a designated Data Protection Officer (DPO) is appointed to oversee compliance and provide guidance on data protection matters.
            </p>
          </section>

          {/* Links to platform pages + useful external links */}
          <section style={sectionWithPaddingStyle}>
            <h2 style={sectionH2Style}>Useful Links and References</h2>
            <p style={pAfterHeaderStyle}>
              To use the Official UK Voting Platform, please visit the following links:
              <ul style={listStyle}>
                <li><a href="/voter/voting-process" style={linkStyle}>The Voting Process</a></li>
                <li><a href="/voter/register" style={linkStyle}>Register to Vote</a></li>
                <li><a href="/voter/manage-registration" style={linkStyle}>Manage Vote Registration</a></li>
                <li><a href="/voter/voting" style={linkStyle}>Vote Now</a></li>
              </ul>
              <br />
              Further links on UK Electoral Law and Data Protection can be found at the following sources:
              <ul style={listStyle}>
                <li><a href="https://www.electoralcommission.org.uk/voting-and-elections" style={linkStyle} target="_blank" rel="noopener noreferrer">Electoral Commission</a></li>
                <li><a href="https://www.ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/" style={linkStyle} target="_blank" rel="noopener noreferrer">Information Commissioner's Office</a></li>
                <li><a href="https://www.legislation.gov.uk/eur/2016/679/contents" style={linkStyle} target="_blank" rel="noopener noreferrer">General Data Protection Regulation (GDPR)</a></li>
              </ul>
            </p>
          </section>
        </div>
      </div>
    </div>
  );
};

export default VoterAboutPage;
