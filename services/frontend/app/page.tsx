export default function HomePage(): JSX.Element {
  return (
    <main>
      <h1>Pressure Vessels Prompt Console</h1>
      <p>Submit a prompt to preview the backend response path.</p>
      <form action="/result" method="get">
        <label htmlFor="prompt">Prompt</label>
        <input
          id="prompt"
          name="prompt"
          type="text"
          required
          minLength={1}
          placeholder="Describe the vessel inspection summary"
        />
        <button type="submit">Run Prompt</button>
      </form>
    </main>
  );
}
