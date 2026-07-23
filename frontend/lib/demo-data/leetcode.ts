import type { LeetCodeProblem } from "@/lib/types";

// Hackathon demo-mode fixture — matches LeetCodeProblem exactly, the same
// shape GET /leetcode/problems will return once that route exists. Only
// used when NEXT_PUBLIC_DEMO_MODE is on AND the real call fails (see
// components/leetcode/ProblemList.tsx). Never silently swapped in without
// the "Demo data" badge.
export const DEMO_LEETCODE_PROBLEMS: LeetCodeProblem[] = [
  {
    id: "demo-two-sum",
    title: "Two Sum",
    link: "https://leetcode.com/problems/two-sum/",
    difficulty: "easy",
    tags: ["array", "hash-table"],
  },
  {
    id: "demo-valid-parentheses",
    title: "Valid Parentheses",
    link: "https://leetcode.com/problems/valid-parentheses/",
    difficulty: "easy",
    tags: ["stack", "string"],
  },
  {
    id: "demo-merge-intervals",
    title: "Merge Intervals",
    link: "https://leetcode.com/problems/merge-intervals/",
    difficulty: "medium",
    tags: ["array", "sorting"],
  },
  {
    id: "demo-course-schedule",
    title: "Course Schedule",
    link: "https://leetcode.com/problems/course-schedule/",
    difficulty: "medium",
    tags: ["graph", "topological-sort"],
  },
];
