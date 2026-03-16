export function StatusCard({ title, value }) {
  return (
    <article className="card">
      <p>{title}</p>
      <strong>{value}</strong>
    </article>
  );
}
