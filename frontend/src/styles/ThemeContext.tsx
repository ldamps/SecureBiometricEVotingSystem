import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { lightTheme, darkTheme, type Theme } from './theme';

type ThemeMode = "light" | "dark";

interface ThemeContextValue {
    theme: Theme;
    mode: ThemeMode;
    toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [mode, setMode] = useState<ThemeMode>("light");

    const toggleTheme = useCallback(() => {
        setMode((prevMode) => (prevMode === "light" ? "dark" : "light"));
    }, []);

    const theme = mode === "light" ? lightTheme : darkTheme;

    useEffect(() => {
        const root = document.documentElement;
        root.style.setProperty("--color-primary", theme.colors.primary);
        root.style.setProperty("--color-primary-hover", theme.colors.primaryHover);
        root.style.setProperty("--color-text-inverse", theme.colors.text.inverse);
        root.style.setProperty("--border-radius-lg", theme.borderRadius.lg);
        root.style.setProperty("--shadow-md", theme.colors.shadows.md);
        root.style.setProperty("--shadow-lg", theme.colors.shadows.lg);
    }, [theme]);

    return (
        <ThemeContext.Provider value={{ theme, mode, toggleTheme }}>
            {children}
        </ThemeContext.Provider>
    );
};

export const useTheme = () => {
    const context = useContext(ThemeContext);
    if (!context) {
        throw new Error("useTheme must be used within a ThemeProvider");
    }
    return context;
};