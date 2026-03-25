import { useEffect, useState } from "react";

const API_BASE = "http://127.0.0.1:8000";

const weekdays = [
  { value: 0, label: "Segunda" },
  { value: 1, label: "Terça" },
  { value: 2, label: "Quarta" },
  { value: 3, label: "Quinta" },
  { value: 4, label: "Sexta" },
  { value: 5, label: "Sábado" },
  { value: 6, label: "Domingo" },
];

export default function RouteCityDayPage() {
  const [routes, setRoutes] = useState([]);
  const [cities, setCities] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [links, setLinks] = useState([]);

  const [routeId, setRouteId] = useState("");
  const [cityId, setCityId] = useState("");
  const [weekday, setWeekday] = useState(0);
  const [vehicleId, setVehicleId] = useState("");

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function loadRoutes() {
    const res = await fetch(`${API_BASE}/routes/`);
    setRoutes(await res.json());
  }

  async function loadCities() {
    const res = await fetch(`${API_BASE}/cities/`);
    setCities(await res.json());
  }

  async function loadVehicles() {
    const res = await fetch(`${API_BASE}/vehicles/`);
    setVehicles(await res.json());
  }

  async function loadLinks() {
    const res = await fetch(`${API_BASE}/route-city-day/`);
    setLinks(await res.json());
  }

  useEffect(() => {
    loadRoutes();
    loadCities();
    loadVehicles();
    loadLinks();
  }, []);

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${API_BASE}/route-city-day/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          route_id: Number(routeId),
          city_id: Number(cityId),
          weekday: Number(weekday),
          vehicle_id: vehicleId ? Number(vehicleId) : null,
          neighborhood_id: null, // por enquanto
        }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "Erro ao salvar vínculo");
      }

      await loadLinks();
    } catch (err) {
      console.error(err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div style={{ padding: 20 }}>
      <h1>Vínculo Rota + Cidade + Dia + Caminhão</h1>

      <form onSubmit={handleSubmit} style={{ marginBottom: 20 }}>
        <div>
          <label>Rota: </label>
          <select
            value={routeId}
            onChange={(e) => setRouteId(e.target.value)}
            required
          >
            <option value="">Selecione...</option>
            {routes.map((r) => (
              <option key={r.id} value={r.id}>
                {r.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Cidade: </label>
          <select
            value={cityId}
            onChange={(e) => setCityId(e.target.value)}
            required
          >
            <option value="">Selecione...</option>
            {cities.map((c) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Dia da semana: </label>
          <select
            value={weekday}
            onChange={(e) => setWeekday(e.target.value)}
          >
            {weekdays.map((d) => (
              <option key={d.value} value={d.value}>
                {d.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label>Caminhão (opcional): </label>
          <select
            value={vehicleId}
            onChange={(e) => setVehicleId(e.target.value)}
          >
            <option value="">Sem caminhão definido</option>
            {vehicles.map((v) => (
              <option key={v.id} value={v.id}>
                {v.name} ({v.plate})
              </option>
            ))}
          </select>
        </div>

        {error && <p style={{ color: "red" }}>{error}</p>}

        <button type="submit" disabled={loading}>
          {loading ? "Salvando..." : "Criar vínculo"}
        </button>
      </form>

      <h2>Vínculos cadastrados</h2>
      <ul>
        {links.map((link) => (
          <li key={link.id}>
            Rota #{link.route_id} - Cidade #{link.city_id} - Dia {link.weekday} - Caminhão{" "}
            {link.vehicle_id ?? "nenhum"}
          </li>
        ))}
      </ul>
    </div>
  );
}
