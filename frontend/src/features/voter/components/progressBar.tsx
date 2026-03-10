import { Theme } from "../../../styles/theme";

const ProgressBar = ({ step, theme }: { step: number, theme: Theme }) => {
    return (
        <div style={{ display: "flex", gap: "0.4rem", marginBottom: "1.75rem" }}>
      {[1,2,3,4,5].map(i => (
        <div key={i} style={{
          flex: 1, height: 4, borderRadius: 9999,
          background: i <= step ? theme.colors.bar : theme.colors.border,
          transition: "background 0.3s",
        }}/>
      ))}
    </div>
    )
}

export default ProgressBar;