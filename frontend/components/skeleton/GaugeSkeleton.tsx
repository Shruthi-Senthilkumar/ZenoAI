export function GaugeSkeleton() {
  return (
    <>
      <div className="skel skel-gauge" />
      <div className="skel skel-line w-60" style={{ marginBottom: 18 }} />
      <div className="skel-bar-row">
        {Array.from({ length: 6 }).map((_, i) => (
          <div className="skel" key={i} />
        ))}
      </div>
    </>
  );
}
