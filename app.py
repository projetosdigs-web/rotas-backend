import { useEffect, useState } from "react";
import { api } from "../services/api";

export default function VinculoRotas() {
  const [routes, setRoutes] = useState([]);
  const [vehicles, setVehicles] = useState([]);
  const [cities, setCities] = useState([]);
  const [vinculos, setVinculos] = useState([]);
  
  const [routeId, setRouteId] = useState("");
  const [vehicleId, setVehicleId] = useState("");
  const [cityId, setCityId] = useState(""); 
  const [neighborhood, setNeighborhood] = useState("");
  const [weekday, setWeekday] = useState("");

  useEffect(() => {
    carregarDados();
  }, []);

  async function carregarDados() {
    try {
      // Carrega apenas o que existe no back: Cidades, Rotas e Veículos
      const [resC, resR, resV, resVi] = await Promise.all([
        api.get("/cities/"),
        api.get("/routes/"),
        api.get("/vehicles/"),
        api.get("/route-city-day/")
      ]);
      setCities(resC.data || []);
      setRoutes(resR.data || []);
      setVehicles(resV.data || []);
      setVinculos(resVi.data || []);
    } catch (err) {
      console.error("Erro ao carregar dados", err);
    }
  }

  async function salvar() {
    if (!routeId || !cityId || weekday === "") return alert("Preencha os campos!");
    try {
      await api.post("/route-city-day/", {
        route_id: Number(routeId),
        vehicle_id: vehicleId ? Number(vehicleId) : null,
        city_id: Number(cityId),
        weekday: Number(weekday),
        neighborhood_name: neighborhood
      });
      alert("Vínculo criado!");
      carregarDados();
    } catch (err) { alert("Erro ao salvar"); }
  }

  return (
    <div style={{ padding: 40, fontFamily: "sans-serif" }}>
      <h1>Vínculo de Rotas</h1>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 15 }}>
        <select value={routeId} onChange={e => setRouteId(e.target.value)} style={inputStyle}>
          <option value="">Selecione a rota</option>
          {routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}
        </select>

        <select value={cityId} onChange={e => setCityId(e.target.value)} style={inputStyle}>
          <option value="">Selecione a cidade</option>
          {cities.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>

        {/* Bairro agora é um campo de TEXTO simples */}
        <input 
          placeholder="Digite o bairro" 
          value={neighborhood} 
          onChange={e => setNeighborhood(e.target.value)} 
          style={inputStyle} 
        />

        <select value={vehicleId} onChange={e => setVehicleId(e.target.value)} style={inputStyle}>
          <option value="">Selecione o veículo</option>
          {vehicles.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
        </select>
      </div>
      <button onClick={salvar} style={btnStyle}>Criar vínculo</button>
    </div>
  );
}

const inputStyle = { padding: 12, borderRadius: 10, border: "1px solid #ddd" };
const btnStyle = { marginTop: 20, padding: 15, background: "#403d7c", color: "#fff", border: "none", borderRadius: 10, cursor: "pointer" };
