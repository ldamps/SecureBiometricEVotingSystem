// Light + Dark theme for the e-voting platform

// Shared theme variables
const shared = {
    fonts: {
      body: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`,
      heading: `'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif`,
      mono: `'Fira Code', 'Cascadia Code', Consolas, monospace`,
    },
    fontSizes: {
      xs: "0.75rem",
      sm: "0.875rem",
      base: "1rem",
      lg: "1.125rem",
      xl: "1.25rem",
      "2xl": "1.5rem",
      "3xl": "1.875rem",
      "4xl": "2.25rem",
    },
    fontWeights: {
      normal: 400,
      medium: 500,
      semibold: 600,
      bold: 700,
    },
    spacing: {
      xs: "0.25rem",
      sm: "0.5rem",
      md: "1rem",
      lg: "1.5rem",
      xl: "2rem",
      "2xl": "3rem",
      "3xl": "4rem",
    },
    borderRadius: {
      sm: "0.25rem",
      md: "0.5rem",
      lg: "0.75rem",
      xl: "1rem",
      full: "9999px",
    },
    breakpoints: {
      sm: 640,
      md: 768,
      lg: 1024,
      xl: 1280,
    },
    layout: {
      maxWidth: "1200px",
      navHeight: "56px",
    },
} as const;
  
// Light theme colors
const lightColors = {
    navBackground: "#1B2444",
    navText: "#FFFFFF",
  
    primary: "#1B2444",
    primaryHover: "#141429",
    secondary: "#4F5D8A",
    secondaryHover: "#3E4C73",
    accent: "#F59E0B",
  
    background: "#E4E9FA",
    surface: "#FFFFFF",
    surfaceAlt: "#EEF1FB",
    border: "#C7CDE8",
    button: "#162F62",
    badge: "#E4E9FA",
    bar: "#162F62",
    
    text: {
      primary: "#0F172A",
      secondary: "#364150",
      light: "#94A3B8",
      inverse: "#FFFFFF",
    },
  
    status: {
      success: "#22C55E",
      warning: "#F59E0B",
      error: "#EF4444",
      info: "#3B82F6",
    },
  
    shadows: {
      sm: "0 1px 2px rgba(0, 0, 0, 0.06)",
      md: "0 4px 6px -1px rgba(0, 0, 0, 0.08)",
      lg: "0 10px 15px -3px rgba(0, 0, 0, 0.08)",
    },

    chart: [
      "#1B2444", "#EF4444", "#F59E0B", "#22C55E", "#3B82F6",
      "#8B5CF6", "#EC4899", "#14B8A6", "#F97316", "#6366F1",
    ],
} as const;
  
// Dark theme colors
const darkColors = {
    navBackground: "#1B2444",
    navText: "#FFFFFF",
  
    primary: "#1B2444",
    primaryHover: "#253B61",
    secondary: "#A5B4FC",
    secondaryHover: "#818CF8",
    accent: "#FBBF24",
  
    background: "#0A1228",
    surface: "#1A1F3D",
    surfaceAlt: "#232849",
    border: "#2E3461",
    button: "#162F62",
    badge: "#1A1F3D",
    bar: "#B4B6D4",
  
    text: {
      primary: "#F1F5F9",
      secondary: "#E3E9F1",
      light: "#64748B",
      inverse: "#FFFFFF",
    },
  
    status: {
      success: "#4ADE80",
      warning: "#FBBF24",
      error: "#FB7185",
      info: "#60A5FA",
    },
  
    shadows: {
      sm: "0 1px 2px rgba(0, 0, 0, 0.3)",
      md: "0 4px 6px -1px rgba(0, 0, 0, 0.4)",
      lg: "0 10px 15px -3px rgba(0, 0, 0, 0.4)",
    },

    chart: [
      "#7B8FCC", "#FB7185", "#FBBF24", "#4ADE80", "#60A5FA",
      "#A78BFA", "#F472B6", "#2DD4BF", "#FB923C", "#818CF8",
    ],
} as const;
  
export const lightTheme = { ...shared, colors: lightColors } as const;
export const darkTheme = { ...shared, colors: darkColors } as const;

export type Theme = typeof lightTheme | typeof darkTheme;