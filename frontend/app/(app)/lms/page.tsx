import { StudentProfileCard } from "@/components/lms/StudentProfileCard";
import { SubjectsCard } from "@/components/lms/SubjectsCard";
import { QuizScoresCard } from "@/components/lms/QuizScoresCard";
import { AssignmentsCard } from "@/components/lms/AssignmentsCard";
import { ProgrammingProgressCard } from "@/components/lms/ProgrammingProgressCard";
import { ExamScheduleCard } from "@/components/lms/ExamScheduleCard";

// No backend connector exists yet for any of these (Subhiksha's unbuilt
// scope) — every card below hits its documented-but-not-yet-live endpoint
// path independently and renders an honest "not connected" state. See the
// final report for the blocked-on note. Attendance is intentionally not a
// card here — dropped from scope for this build even though it's a
// seventh connector method in the original PRD/Integration Spec.
export default function LmsPage() {
  return (
    <section className="tab-panel active" id="tab-lms">
      <div className="section-label">LMS Connector — profile, coursework, schedule</div>
      <div className="lms-grid">
        <StudentProfileCard />
        <SubjectsCard />
        <QuizScoresCard />
        <AssignmentsCard />
        <ProgrammingProgressCard />
        <ExamScheduleCard />
      </div>
    </section>
  );
}
