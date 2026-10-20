type PlaceholderPageProps = {
  title: string;
};

export function PlaceholderPage({ title }: PlaceholderPageProps) {
  return (
    <>
      <div className="top-bar">
        <h1>{title}</h1>
      </div>
      <p className="date-tag">This screen is built in a later step.</p>
      <div className="card">Coming soon</div>
    </>
  );
}
