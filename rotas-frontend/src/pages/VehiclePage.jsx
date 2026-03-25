import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000"; // ajuste se estiver em outra porta/host

export default function VehiclePage() {
  const [vehicles, setVehicles] = useState([]);
  const [name, setName] = useState("");
  const [plate, setPlate] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadVehicles() {
    try {
      const res = await fetch(`${API_BASE}/vehicles/`);
      const data = await res.json();
      setVehicles(data);
    } catch (err) {
      console.error(err);
      setError("Erro ao carregar veículos");
    }
  }

  useEffect(() => {
    loadVehicles();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/vehicles/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name,
          plate,
          active: 1,
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Erro ao salvar");
      }

      setName("");
      setPlate("");
      await loadVehicles();
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Caminhões</h1>

      <form onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
        <div>
          <label>Nome do caminhão: </label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>

        <div>
          <label>Placa: </label>
          <input
            value={plate}
            onChange={(e) => setPlate(e.target.value)}
          />
        </div>

        {error && <p style={{ color: "red" }}>{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Salvando..." : "Cadastrar"}
        </button>
      </form>

      <h2>Lista de caminhões</h2>
      <ul>
        {vehicles.map((v) => (
          <li key={v.id}>
            #{v.id} - {v.name} ({v.plate || "sem placa"})
          </li>
        ))}
      </ul>
    </div>
  );
}
