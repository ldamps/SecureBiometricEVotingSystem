import React from "react";
import { useTheme } from "../../styles/ThemeContext";
import {
    getLinkStyle,
    getSectionStarStyle,
    getH3Style,
    getPAfterHeaderStyle,
    getHeaderH1Style,
    getFirstSectionStyle,
    getSectionH2Style,
    getSectionWithPaddingStyle,
    getListStyle,
} from "./voterAboutPage.styles";

const VoterAboutPage: React.FC = () => {
    const { theme } = useTheme();
    const linkStyle = getLinkStyle(theme);
    const h3Style = getH3Style(theme);
    const pAfterHeaderStyle = getPAfterHeaderStyle(theme);
    const headerH1Style = getHeaderH1Style(theme);
    const firstSectionStyle = getFirstSectionStyle(theme);
    const sectionH2Style = getSectionH2Style(theme);
    const sectionWithPaddingStyle = getSectionWithPaddingStyle(theme);
    const listStyle = getListStyle(theme);
    const sectionStarStyle = getSectionStarStyle(theme);

    const sectionStar = (
        <svg width="0.65em" height="0.65em" viewBox="0 0 24 24" style={sectionStarStyle} aria-hidden>
            <path d="M12 2l2.4 7.4h7.6l-6 4.6 2.3 7-6.3-4.6-6.3 4.6 2.3-7-6-4.6h7.6z" />
        </svg>
    );

    return (
        <div>
            <style>{`
                .voter-about-page a:hover { color: ${theme.colors.primaryHover}; }
            `}</style>
            <div className="voter-about-page">
                <header>
                    <h1 style={headerH1Style}>About the Platform</h1>
                </header>

                {/* About the platform */}
                <section style={firstSectionStyle}>
                    <p>
                        The Official UK Voting Platform is committed to delivering a secure, acessible and legally compliant E-Voting platform that enables eligible voters across the UK to register, manage their electoral details and cast their vote using their own trusted devices. Our purpose is to modernise participation in demoratic processes while upholding the highest standards of integrity, confidentiality and public trust.
                        <br/>
                        <br/>
                        Accessibility and security are fundamental to our approach. Every aspect of our platform has been designed to ensure that convenience never compromises legal compliance or electoral integrity.
                    </p>
                </section>

                { /* Our committtment to Data Protection in the UK */}
                <section style={sectionWithPaddingStyle}>
                    <h2 style={sectionH2Style}>Our committtment to Data Protection in the UK</h2>
                    <p style={pAfterHeaderStyle}>
                        The protection of personal data is central to our operations. We process information strictly in accordance with the UK General Protection Regulation (UK GDPR) and the Data Protection Act 2018. Our practices are guided by regulatory expetations set out by the Information Commissioner's Office (ICO).
                        <br/>
                        We adhere to the core principles of UK data protection law:
                        <ul style={listStyle}>
                            <li>
                                <strong>Lawfulness, fairness and transparency:</strong> Personal data is processed only where a clear lawful basis applies
                            </li>
                            <li>
                                <strong>Purpose limitation:</strong> Information is collected for specific, legitimate and lawful purposes only
                            </li>
                            <li>
                                <strong>Data minimisation:</strong> Only the minimum amount of data necessary is collected and processed
                            </li>
                            <li>
                                <strong>Accuracy:</strong> Data is kept up to date and accurate
                            </li>
                            <li>
                                <strong>Storage limitation:</strong> Data is stored for no longer than necessary
                            </li>
                            <li>
                                <strong>Integrity and confidentiality:</strong> Data is protected against unauthorised access and disclosure
                            </li>
                        </ul>
                    </p>

                    <h3 style={h3Style}>
                        {sectionStar}
                        Privacy by Design
                    </h3>
                    <p style={pAfterHeaderStyle}>
                        Data protection is embedded into our platform architecture. Through privacy-by-design and privacy-by-default practices, we ensure that:
                        <ul style={listStyle}>
                            <li><strong>Only essential data is collected and processed</strong></li>
                            <li><strong>Access to data is strictly role-based and access controls are enforced</strong></li>
                            <li><strong>Encryption protects sensitive data in transit and at rest</strong></li>
                            <li><strong>Multi-factor authentication protects against unauthorized access</strong></li>
                            <li><strong>Continuous monitoring and audit trails are in place</strong></li>
                        </ul>
                        Where processing activites present high ricks to individual rights and freedoms, we conduct Data Protection Impact Assessments (DPIAs) in accordance with UK GDPR requirements.
                    </p>

                    <h3 style={h3Style}>
                        {sectionStar}
                        Transparency and Individual Rights
                    </h3>
                    <p style={pAfterHeaderStyle}>
                        The Official UK Voting Platform is committed to oppeness about how personal data is used. Clear privacy notices explain:
                        <ul style={listStyle}>
                            <li>What data is collected</li>
                            <li>Why it is collected</li>
                            <li>How long it is retained</li>
                            <li>How it is protected</li>
                        </ul>
                        Individual rights are fully upheld under UK GDPR, including the right of access, rectification, restriction, objection and where applicable, erasure. Procedures are in place to respond to requests within statutory timeframes.
                        <br/>
                        <br/>
                        In the unlikely event of a personal data breach, we follow established incident response procedures and where legally required, notify the Information Commissioner's Office within the mandated timeframe.
                    </p>

                    <h3 style={h3Style}>
                        {sectionStar}
                        Accountability and Governance
                    </h3>
                    <p style={pAfterHeaderStyle}>
                        We maintain robust governance frameworks to ensure compliance, including:
                        <ul style={listStyle}>
                            <li>Documented reocrds of data processing activities</li>
                            <li>Internal audit and compliance procedures</li>
                        </ul>
                        Where required, a designated Data Protection Officer (DPO) is appointed to oversee compliance and provide guidance on data protection matters.
                    </p>
                </section>

                { /* Links to platform pages + useful external links */ }
                <section style={sectionWithPaddingStyle}>
                    <h2 style={sectionH2Style}>Useful Links and References</h2>
                    <p style={pAfterHeaderStyle}>
                        To use the Official UK Voting Platform, please visit the following links:
                        <ul style={listStyle}>
                            <li><a href="/voter/voting-process" style={linkStyle}>The Voting Process</a></li>
                            <li><a href="/voter/register" style={linkStyle}>Register to Vote</a></li>
                            <li><a href="/" style={linkStyle}>Manage Vote Registration</a></li>
                            <li><a href="/" style={linkStyle}>Vote Now</a></li>
                        </ul>
                        <br/>
                        Further links on UK Electoral Law and Data Protection can be found at the following sources:
                        <ul style={listStyle}>
                            <li>
                                <a href="https://www.electoralcommission.org.uk/voting-and-elections" style={linkStyle} target="_blank" rel="noopener noreferrer">Electoral Commission</a>
                            </li>
                            <li>
                                <a href="https://www.ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/" style={linkStyle} target="_blank" rel="noopener noreferrer">Information Commissioner's Office</a>
                            </li>
                            <li>
                                <a href="https://www.legislation.gov.uk/eur/2016/679/contents" style={linkStyle} target="_blank" rel="noopener noreferrer">General Data Protection Regulation (GDPR)</a>
                            </li>
                        </ul>
                    </p>
                </section>
            </div>
        </div>
    );
};

export default VoterAboutPage;
