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
        },
    },
    plugins: [],
};
