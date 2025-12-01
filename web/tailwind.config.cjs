module.exports = {
    content: ["./index.html", "./src/**/*.{ts,tsx}"],
    theme: {
        extend: {
            colors: {
                primary: "#2563eb",
                success: "#16a34a",
                danger: "#dc2626",
                muted: "#64748b",
                surface: "#ffffff",
                card: "#f8fafc",
            },
            borderRadius: {
                md: "12px",
                lg: "16px",
            },
            keyframes: {
                "reload-spin": {
                    "0%": { transform: "rotate(0deg)" },
                    "70%": { transform: "rotate(355deg)" },
                    "100%": { transform: "rotate(360deg)" },
                },
            },
            animation: {
                "reload-spin":
                    "reload-spin 0.6s cubic-bezier(0.4, 0, 0.2, 1) infinite",
            },
        },
    },
    plugins: [],
};
