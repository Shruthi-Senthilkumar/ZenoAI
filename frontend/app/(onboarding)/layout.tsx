import "../../styles/app-shell.css";

// No StudentStoreProvider here — intake runs before a student has any
// shared app state to read or write (Frontend Spec §5.1: "nothing outside
// app/(app)/layout.tsx pays for store creation it doesn't use"). It posts
// directly to /intake/turn and redirects into app/(app) on completion,
// where the provider actually lives.
export default function OnboardingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div style={{ minHeight: "100vh", background: "var(--base)", color: "var(--ink)" }}>{children}</div>;
}
