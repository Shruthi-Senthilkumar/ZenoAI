import { ProblemList } from "@/components/leetcode/ProblemList";

// Required, visible feature (item 10) — its own route, not folded into
// Dashboard's table alone. No live backend yet (GET /leetcode/problems,
// POST /leetcode/{id}/push-confirm are both unbuilt), so with
// NEXT_PUBLIC_DEMO_MODE on this renders fixture data behind a loud "Demo
// data" badge rather than sitting blank for a hackathon demo — see
// components/leetcode/ProblemList.tsx.
export default function LeetCodePage() {
  return (
    <section className="tab-panel active" id="tab-leetcode">
      <div className="section-label">LeetCode Tracker</div>
      <ProblemList />
    </section>
  );
}
