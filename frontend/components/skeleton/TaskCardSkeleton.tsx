export function TaskCardSkeleton({ count = 3 }: { count?: number }) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div className="skel-task-card" key={i}>
          <div className="skel skel-badge" />
          <div className="skel-lines">
            <div className="skel skel-line w-60" />
            <div className="skel skel-line w-40" />
          </div>
          <div className="skel skel-btn" />
        </div>
      ))}
    </>
  );
}
