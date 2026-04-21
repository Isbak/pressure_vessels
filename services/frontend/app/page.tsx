export default function HomePage(): JSX.Element {
  return (
    <main>
      <h1>Pressure Vessel Design Run Console</h1>
      <p>Submit baseline design inputs and view workflow/compliance status.</p>
      <form action="/result" method="get">
        <label htmlFor="designPressureBar">Design pressure (bar)</label>
        <input
          id="designPressureBar"
          name="designPressureBar"
          type="number"
          step="0.1"
          min="0.1"
          required
          defaultValue="18"
        />

        <label htmlFor="designTemperatureC">Design temperature (°C)</label>
        <input
          id="designTemperatureC"
          name="designTemperatureC"
          type="number"
          step="0.1"
          required
          defaultValue="65"
        />

        <label htmlFor="volumeM3">Volume (m³)</label>
        <input
          id="volumeM3"
          name="volumeM3"
          type="number"
          step="0.1"
          min="0.1"
          required
          defaultValue="30"
        />

        <label htmlFor="code">Design code</label>
        <input
          id="code"
          name="code"
          type="text"
          required
          minLength={2}
          defaultValue="ASME Section VIII Div 1"
        />

        <button type="submit">Start Design Run</button>
      </form>
    </main>
  );
}
