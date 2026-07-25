import { Component } from "react";
import { T } from "../styles/theme";

/**
 * Error boundary to catch rendering errors in the component tree
 * and display a fallback UI instead of a blank white page.
 */
export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            background: T.bg,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flexDirection: "column",
            gap: 16,
            padding: 40,
          }}
        >
          <div style={{ fontSize: 48 }}>⚠️</div>
          <h2 style={{ color: T.textPrimary, margin: 0, fontSize: 20 }}>
            Something went wrong
          </h2>
          <p style={{ color: T.textMuted, fontSize: 14, textAlign: "center", maxWidth: 400 }}>
            {this.state.error?.message || "An unexpected error occurred while rendering this page."}
          </p>
          <button
            onClick={() => {
              this.setState({ hasError: false, error: null });
              window.location.href = "/dashboard";
            }}
            style={{
              padding: "10px 24px",
              background: T.accent,
              color: "#fff",
              border: "none",
              borderRadius: 8,
              fontSize: 14,
              cursor: "pointer",
              fontWeight: 500,
            }}
          >
            Go to Dashboard
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
