import { useState, useEffect } from "react";
import { MapContainer, TileLayer, Marker, Popup, Polyline } from "react-leaflet";
import L from "leaflet";

const API_BASE = `http://${window.location.hostname}:8000`;

const WEEKDAYS = {
  0: "Segunda-feira",
  1: "Terça-feira",
  2: "Quarta-feira",
  3: "Quinta-feira",
  4: "Sexta-feira",
  7: "Todos os dias (Diário)",
};

const getDayStatus = (routeWeekday) => {
  const jsDate = new Date();
  const jsDay = jsDate.getDay(); 
  let currentSystemDay = jsDay === 0 ? -1 : jsDay - 1; 
  if (jsDay === 6) currentSystemDay = 99; 

  if (routeWeekday === 7) return { text: "Todo dia", color: "bg-blue-600 text-white" };
  if (routeWeekday === currentSystemDay) return { text: "HOJE", color: "bg-emerald-500 text-white animate-pulse font-bold" };
  
  let tomorrowSystemDay = currentSystemDay + 1;
  if (currentSystemDay >= 4 || currentSystemDay === -1) tomorrowSystemDay = 0; 
  
  if (routeWeekday === tomorrowSystemDay) return { text: "Próximo Dia Útil", color: "bg-amber-500 text-slate-900 font-bold" };
  
  const label = WEEKDAYS[routeWeekday] ? WEEKDAYS[routeWeekday].split('-')[0] : "Indefinido";
  return { text: label, color: "bg-slate-700 text-slate-300" };
};

const cityIcon = new L.Icon({
  iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowSize: [41, 41],
});

function LoginScreen({ onLoginSuccess }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    if (!username.trim() || !password.trim()) { setError("Informe usuário e senha."); return; }
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/auth/login`, {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ username: username.trim(), password }),
      });
      if (!resp.ok) { setError("Usuário ou senha incorretos."); return; }
      const data = await resp.json();
      onLoginSuccess(data.access_token);
    } catch { setError("Erro de conexão com o servidor."); } 
    finally { setLoading(false); }
  };

  return (
    <div className="w-full flex flex-col items-center justify-center py-10">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-xl p-6 space-y-6">
        <div className="text-center space-y-2">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-emerald-500/20 border border-emerald-400/60 text-2xl">🔒</div>
          <h1 className="text-2xl font-bold">Acesso Faturamento</h1>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <input type="text" value={username} placeholder="Usuário" onChange={(e) => setUsername(e.target.value)} className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white" />
          <input type="password" value={password} placeholder="Senha" onChange={(e) => setPassword(e.target.value)} className="w-full px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 text-white" />
          {error && <div className="text-red-400 text-sm">{error}</div>}
          <button type="submit" disabled={loading} className="w-full mt-2 px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 font-bold text-slate-950 transition">
            {loading ? "Entrando..." : "Acessar Painel"}
          </button>
        </form>
      </div>
    </div>
  );
}

function RouteCitiesMap({ data }) {
  const valid = (data || []).filter((item) => item.latitude != null && item.longitude != null);
  if (valid.length === 0) return <p className="text-sm text-slate-400">Sem coordenadas para exibir no mapa.</p>;

  const groupedRoutes = {};
  valid.forEach((item) => {
    if (!groupedRoutes[item.route_name]) groupedRoutes[item.route_name] = [];
    groupedRoutes[item.route_name].push([item.latitude, item.longitude]);
  });

  const getColor = (str) => {
    let hash = 0;
    for (let i = 0; i < str.length; i++) hash = str.charCodeAt(i) + ((hash << 5) - hash);
    const c = (hash & 0x00ffffff).toString(16).toUpperCase();
    return "#" + "00000".substring(0, 6 - c.length) + c;
  };

  const center = [valid[0].latitude, valid[0].longitude];

  return (
    <div className="mt-4 h-96 w-full rounded-xl overflow-hidden border border-slate-800 shadow-inner relative z-0">
      <MapContainer center={center} zoom={8} style={{ height: "100%", width: "100%" }}>
        <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution="© OpenStreetMap contributors" />
        {Object.keys(groupedRoutes).map((routeName, idx) => (
          <Polyline key={`line-${idx}`} positions={groupedRoutes[routeName]} pathOptions={{ color: getColor(routeName), weight: 4, opacity: 0.7, dashArray: "10, 10" }} />
        ))}
        {valid.map((item, idx) => (
          <Marker key={idx} position={[item.latitude, item.longitude]} icon={cityIcon}>
            <Popup>
              <div className="space-y-1 text-sm min-w-[180px]">
                <strong className="text-emerald-600 block text-base border-b pb-1 mb-1">{item.city_name}</strong>
                <div>Rota: {item.route_name}</div>
                <div>Veículo: {item.vehicle_name || "-"}</div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}

function App() {
  const [token, setToken] = useState(() => localStorage.getItem("token") || "");
  const [activeTab, setActiveTab] = useState("consulta");

  const [cityQuery, setCityQuery] = useState(""); const [result, setResult] = useState(null); const [loading, setLoading] = useState(false); const [error, setError] = useState("");
  const [weekday, setWeekday] = useState(""); const [resultByDay, setResultByDay] = useState([]); const [loadingDay, setLoadingDay] = useState(false); const [errorDay, setErrorDay] = useState("");

  const [routes, setRoutes] = useState([]); const [cities, setCities] = useState([]); const [links, setLinks] = useState([]); const [neighborhoods, setNeighborhoods] = useState([]); const [vehicles, setVehicles] = useState([]);

  // 🔥 Estados dos Buscadores (Filtros)
  const [filterRoute, setFilterRoute] = useState("");
  const [filterCity, setFilterCity] = useState("");
  const [filterNb, setFilterNb] = useState("");
  const [filterVehicle, setFilterVehicle] = useState("");
  const [filterLink, setFilterLink] = useState("");

  const [newRouteName, setNewRouteName] = useState(""); const [newRouteDesc, setNewRouteDesc] = useState("");
  const [newCityName, setNewCityName] = useState(""); const [newCityState, setNewCityState] = useState(""); const [newCityLat, setNewCityLat] = useState(""); const [newCityLng, setNewCityLng] = useState(""); const [cityMsg, setCityMsg] = useState(""); const [citySuggestions, setCitySuggestions] = useState([]); const [loadingCityGeo, setLoadingCityGeo] = useState(false);
  const [linkRouteId, setLinkRouteId] = useState(""); const [linkCityId, setLinkCityId] = useState(""); const [linkNeighborhoodId, setLinkNeighborhoodId] = useState(""); const [linkWeekday, setLinkWeekday] = useState(""); const [linkVehicleId, setLinkVehicleId] = useState(""); const [linkMsg, setLinkMsg] = useState("");
  const [nbCityId, setNbCityId] = useState(""); const [nbName, setNbName] = useState(""); const [nbLat, setNbLat] = useState(""); const [nbLng, setNbLng] = useState(""); const [nbMsg, setNbMsg] = useState(""); const [nbSuggestions, setNbSuggestions] = useState([]); const [nbLoading, setNbLoading] = useState(false);
  const [newVehicleName, setNewVehicleName] = useState(""); const [newVehiclePlate, setNewVehiclePlate] = useState(""); const [vehicleMsg, setVehicleMsg] = useState("");

  const authHeaders = token ? { Authorization: `Bearer ${token}` } : {};

  const getRouteName = (id) => routes.find((r) => r.id === id)?.name || `Rota ${id}`;
  const getCityName = (id) => { const c = cities.find((c) => c.id === id); return c ? c.name : `Cidade ${id}`; };
  const getVehicleName = (id) => vehicles.find((v) => v.id === id)?.name || "Sem caminhão";
  const getNeighborhoodName = (id) => neighborhoods.find((n) => n.id === id)?.name || "Bairro";

  useEffect(() => {
    if (!token) return;
    const fetchInitialData = async () => {
      try {
        const [r, c, l, n, v] = await Promise.all([
          fetch(`${API_BASE}/routes/`, { headers: authHeaders }), fetch(`${API_BASE}/cities/`, { headers: authHeaders }),
          fetch(`${API_BASE}/route-city-day/`, { headers: authHeaders }), fetch(`${API_BASE}/neighborhoods/`, { headers: authHeaders }), fetch(`${API_BASE}/vehicles/`, { headers: authHeaders })
        ]);
        if (r.ok) setRoutes(await r.json()); if (c.ok) setCities(await c.json()); if (l.ok) setLinks(await l.json());
        if (n.ok) setNeighborhoods(await n.json()); if (v.ok) setVehicles(await v.json());
      } catch (err) { console.error(err); }
    };
    fetchInitialData();
  }, [token]);

  const handleLoginSuccess = (newToken) => { setToken(newToken); localStorage.setItem("token", newToken); };
  const handleLogout = () => { setToken(""); localStorage.removeItem("token"); setActiveTab("consulta"); };

  const handleSearch = async () => {
    setError(""); setResult(null);
    if (!cityQuery.trim()) { setError("Digite o nome."); return; }
    setLoading(true);
    try {
      const resp = await fetch(`${API_BASE}/lookup-city/?query=${encodeURIComponent(cityQuery.trim())}`, { headers: authHeaders });
      if (!resp.ok) { setError(resp.status === 404 ? "Não encontrado." : "Erro ao consultar."); return; }
      setResult(await resp.json());
    } catch { setError("Erro de conexão."); } finally { setLoading(false); }
  };
  const handleClearCitySearch = () => { setCityQuery(""); setResult(null); setError(""); };

  const handleSearchByDay = async () => {
    setErrorDay(""); setResultByDay([]);
    if (weekday === "") { setErrorDay("Selecione um dia."); return; }
    setLoadingDay(true);
    try {
      const resp = await fetch(`${API_BASE}/lookup-day/?weekday=${weekday}`, { headers: authHeaders });
      if (resp.ok) setResultByDay(await resp.json());
      else setErrorDay("Erro ao consultar.");
    } catch { setErrorDay("Erro de conexão."); } finally { setLoadingDay(false); }
  };
  const handleClearDaySearch = () => { setWeekday(""); setResultByDay([]); setErrorDay(""); };

  const apiRequest = async (endpoint, method, body, onSuccess, successMsg) => {
    try {
      const resp = await fetch(`${API_BASE}/${endpoint}`, {
        method,
        headers: { "Content-Type": "application/json", ...authHeaders },
        body: body ? JSON.stringify(body) : null
      });

      if (resp.ok) {
        if (method !== "DELETE") { const data = await resp.json(); onSuccess(data); } else { onSuccess(); }
        alert("✅ " + successMsg);
      } else {
        if (resp.status === 401) { alert("🔒 SESSÃO EXPIRADA!\nSeu token venceu. Faça login novamente."); } 
        else { const err = await resp.json().catch(() => ({ detail: "Erro desconhecido" })); alert(`❌ ERRO: ${err.detail}`); }
      }
    } catch (e) { alert("❌ ERRO DE CONEXÃO: Verifique se o servidor está rodando."); }
  };

  const handleCreateRoute = () => {
    if (!newRouteName.trim()) { alert("⚠️ Digite o nome da rota."); return; }
    apiRequest("routes/", "POST", { name: newRouteName, description: newRouteDesc }, (saved) => { setRoutes(p => [...p, saved]); setNewRouteName(""); setNewRouteDesc(""); }, "Rota cadastrada!");
  };
  const handleDeleteRoute = (id) => {
    if (!window.confirm("🗑️ Excluir esta rota? (Certifique-se de que não há vínculos)")) return;
    apiRequest(`routes/${id}`, "DELETE", null, () => setRoutes(p => p.filter(x => x.id !== id)), "Rota excluída!");
  };

  const handleCreateCity = () => {
    if (!newCityName.trim()) { alert("⚠️ Digite o nome da cidade."); return; }
    const lat = parseFloat(newCityLat.replace(",", ".")); const lng = parseFloat(newCityLng.replace(",", "."));
    if (isNaN(lat) || isNaN(lng)) { alert("⚠️ Erro GPS: Preencha latitude e longitude."); return; }
    apiRequest("cities/", "POST", { name: newCityName, latitude: lat, longitude: lng }, (saved) => { setCities(p => [...p, saved]); setNewCityName(""); setCitySuggestions([]); }, "Cidade cadastrada!");
  };
  const handleDeleteCity = (id) => {
    if (!window.confirm("🗑️ Excluir cidade? (Certifique-se de que não há vínculos)")) return;
    apiRequest(`cities/${id}`, "DELETE", null, () => setCities(p => p.filter(x => x.id !== id)), "Cidade excluída!");
  };

  const handleCreateNeighborhood = () => {
    if (!nbCityId) { alert("⚠️ Selecione a cidade."); return; }
    if (!nbName.trim()) { alert("⚠️ Digite o nome do bairro."); return; }
    const lat = parseFloat(String(nbLat).replace(",", ".")); const lng = parseFloat(String(nbLng).replace(",", "."));
    if (isNaN(lat) || isNaN(lng)) { alert("⚠️ Erro GPS: Clique em 'Buscar GPS' antes de salvar."); return; }
    apiRequest("neighborhoods/", "POST", { name: nbName, city_id: Number(nbCityId), latitude: lat, longitude: lng }, (saved) => { setNeighborhoods(p => [...p, saved]); setNbName(""); setNbSuggestions([]); }, "Bairro cadastrado!");
  };
  const handleDeleteNeighborhood = (id) => {
    if (!window.confirm("🗑️ Excluir bairro?")) return;
    apiRequest(`neighborhoods/${id}`, "DELETE", null, () => setNeighborhoods(p => p.filter(x => x.id !== id)), "Bairro excluído!");
  };

  const handleCreateVehicle = () => {
    if (!newVehicleName.trim()) { alert("⚠️ Digite o nome do veículo."); return; }
    apiRequest("vehicles/", "POST", { name: newVehicleName, plate: newVehiclePlate, active: 1 }, (saved) => { setVehicles(p => [...p, saved]); setNewVehicleName(""); setNewVehiclePlate(""); }, "Veículo cadastrado!");
  };
  const handleDeleteVehicle = (id) => {
    if (!window.confirm("🗑️ Excluir veículo?")) return;
    apiRequest(`vehicles/${id}`, "DELETE", null, () => setVehicles(p => p.filter(x => x.id !== id)), "Veículo excluído!");
  };

  const handleLinkRouteCityDay = () => {
    if (!linkRouteId || !linkCityId || linkWeekday === "") { alert("⚠️ Preencha Rota, Cidade e Dia."); return; }
    apiRequest("route-city-day/", "POST", { route_id: Number(linkRouteId), city_id: Number(linkCityId), weekday: Number(linkWeekday), vehicle_id: linkVehicleId ? Number(linkVehicleId) : null, neighborhood_id: linkNeighborhoodId ? Number(linkNeighborhoodId) : null }, (saved) => setLinks(p => [...p, saved]), "Vínculo criado!");
  };
  const handleDeleteLink = (id) => {
    if (!window.confirm("🗑️ Remover este vínculo?")) return;
    apiRequest(`route-city-day/${id}`, "DELETE", null, () => setLinks(p => p.filter(x => x.id !== id)), "Vínculo removido!");
  };

  const handleGeocode = async (query, cityId, setSugg, setLoad, setMsg) => {
    if (!query) { alert("Digite o nome para buscar GPS."); return; }
    setLoad(true);
    let url = `${API_BASE}/geocode/?query=${encodeURIComponent(query)}`;
    if (cityId) { const c = cities.find(x => x.id === Number(cityId)); if (c) url += `&city_name=${encodeURIComponent(c.name)}`; }
    try { const r = await fetch(url, { headers: authHeaders }); if (r.ok) setSugg(await r.json()); else alert("Erro ao buscar GPS."); } catch { alert("Erro conexão GPS."); } finally { setLoad(false); }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex justify-center items-start px-4 py-6 font-sans">
      <div className="w-full max-w-6xl bg-slate-950 border border-slate-800 rounded-2xl shadow-2xl p-6">
        <header className="flex flex-wrap items-center justify-between gap-4 mb-8 pb-6 border-b border-slate-800/50">
          <div><h1 className="text-3xl font-bold tracking-tight text-emerald-400 flex items-center gap-3">🚚 Sistema de Rotas</h1></div>
          <div className="flex items-center gap-3">
            <div className="flex bg-slate-900 border border-slate-700 rounded-full p-1">
              {['consulta', 'admin'].map(tab => (
                <button key={tab} onClick={() => setActiveTab(tab)} className={`px-5 py-1.5 text-sm rounded-full transition-all ${activeTab === tab ? "bg-emerald-600 text-white font-bold shadow-lg" : "text-slate-400 hover:text-slate-200"}`}>{tab === 'consulta' ? 'Consulta' : 'Administração'}</button>
              ))}
            </div>
            {token && <button onClick={handleLogout} className="px-4 py-1.5 rounded-full text-xs font-bold bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20">SAIR</button>}
          </div>
        </header>

        {activeTab === "consulta" && (
          <div className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              
              <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-200 mb-3">🔍 Por Cidade/Bairro</h2>
                <div className="flex gap-2">
                  <input type="text" placeholder="Ex: Campinas" value={cityQuery} onChange={e => setCityQuery(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()} className="flex-1 px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 focus:border-emerald-500 outline-none" />
                  <button onClick={handleSearch} disabled={loading} className="px-4 py-2 bg-emerald-600 rounded-lg font-bold hover:bg-emerald-500 transition">{loading ? "..." : "Buscar"}</button>
                  {(result || cityQuery) && (<button onClick={handleClearCitySearch} className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition">✕</button>)}
                </div>
                {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
                {result && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2">
                    <div className="mb-2 text-emerald-400 font-bold">{result.city} <span className="text-slate-500 font-normal text-xs">({result.city_type})</span></div>
                    <div className="overflow-hidden rounded-lg border border-slate-700 bg-slate-900">
                      <table className="w-full text-sm text-left"><thead className="bg-slate-800 text-slate-400 uppercase text-xs"><tr><th className="py-2 px-4">Status</th><th className="py-2 px-4">Rota</th><th className="py-2 px-4">Local</th><th className="py-2 px-4">Veículo</th></tr></thead><tbody className="divide-y divide-slate-800">{result.routes.map((r, i) => { const st = getDayStatus(r.weekday); return (<tr key={i} className="hover:bg-slate-800/50"><td className="py-2 px-4"><span className={`px-2 py-0.5 rounded text-xs font-bold ${st.color}`}>{st.text}</span></td><td className="py-2 px-4 font-semibold text-emerald-400">{r.route_name}</td><td className="py-2 px-4 text-slate-300">{r.neighborhood_name || "Cidade inteira"}</td><td className="py-2 px-4 text-slate-400 font-mono text-xs">{r.vehicle_name || "-"}</td></tr>) })}</tbody></table>
                    </div>
                    <RouteCitiesMap data={result.routes} />
                  </div>
                )}
              </section>

              <section className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-200 mb-3">📅 Por Dia</h2>
                <div className="flex gap-2">
                  <select value={weekday} onChange={e => setWeekday(e.target.value)} className="flex-1 px-3 py-2 rounded-lg bg-slate-950 border border-slate-700 focus:border-emerald-500 outline-none">
                    <option value="">Selecione o dia...</option>
                    <option value="7">Todos os dias (Diário)</option>
                    {Object.entries(WEEKDAYS).filter(([k]) => k !== '7').map(([k, v]) => <option key={k} value={k}>{v}</option>)}
                  </select>
                  <button onClick={handleSearchByDay} disabled={loadingDay} className="px-4 py-2 bg-emerald-600 rounded-lg font-bold hover:bg-emerald-500 transition">{loadingDay ? "..." : "Ver"}</button>
                  {(resultByDay.length > 0 || weekday) && (<button onClick={handleClearDaySearch} className="px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-300 hover:bg-slate-700 hover:text-white transition">✕</button>)}
                </div>
                {resultByDay.length > 0 && (
                  <div className="mt-4 animate-in fade-in slide-in-from-top-2">
                    <div className="mb-2 text-emerald-400 font-bold">Logística: {WEEKDAYS[weekday]}</div>
                    <div className="overflow-hidden rounded-lg border border-slate-700 bg-slate-900">
                      <table className="w-full text-sm text-left"><thead className="bg-slate-800 text-slate-400 uppercase text-xs"><tr><th className="py-2 px-4">Status</th><th className="py-2 px-4">Rota</th><th className="py-2 px-4">Cidade/Bairro</th><th className="py-2 px-4">Veículo</th></tr></thead><tbody className="divide-y divide-slate-800">{resultByDay.map((r, i) => { const st = getDayStatus(r.weekday); return (<tr key={i} className="hover:bg-slate-800/50"><td className="py-2 px-4"><span className={`px-2 py-0.5 rounded text-xs font-bold ${st.color}`}>{st.text}</span></td><td className="py-2 px-4 font-semibold text-emerald-400">{r.route_name}</td><td className="py-2 px-4 text-slate-300">{r.city_name} {r.neighborhood_name && `- ${r.neighborhood_name}`}</td><td className="py-2 px-4 text-slate-400 font-mono text-xs">{r.vehicle_name || "-"}</td></tr>) })}</tbody></table>
                    </div>
                    <RouteCitiesMap data={resultByDay} />
                  </div>
                )}
              </section>
            </div>
          </div>
        )}

        {activeTab === "admin" && (
          !token ? <LoginScreen onLoginSuccess={handleLoginSuccess} /> : (
            <div className="space-y-6 animate-in fade-in">
              <div className="bg-slate-900/50 p-4 rounded-lg border border-slate-800">
                 <h2 className="text-xl font-bold text-slate-200 mb-4">Painel de Cadastro</h2>
                 
                 {/* 1. ROTAS */}
                 <div className="mb-6 pb-6 border-b border-slate-800">
                   <h3 className="text-emerald-400 font-bold mb-2">1. Rotas</h3>
                   <div className="flex flex-wrap gap-2 mb-3"><input className="input-admin" placeholder="Nome" value={newRouteName} onChange={e => setNewRouteName(e.target.value)} /><button className="btn-save" onClick={handleCreateRoute}>Salvar</button></div>
                   
                   {/* Filtro Rotas */}
                   <input className="input-admin w-full mb-2 text-sm bg-slate-800" placeholder="🔍 Filtrar rotas..." value={filterRoute} onChange={e => setFilterRoute(e.target.value)} />
                   
                   <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                     {routes.filter(r => r.name.toLowerCase().includes(filterRoute.toLowerCase())).map(r => (<span key={r.id} className="tag-item">{r.name} <button onClick={() => handleDeleteRoute(r.id)} className="text-red-400 ml-1">x</button></span>))}
                   </div>
                 </div>

                 {/* 2. CIDADES */}
                 <div className="mb-6 pb-6 border-b border-slate-800">
                   <h3 className="text-emerald-400 font-bold mb-2">2. Cidades</h3>
                   <div className="flex flex-wrap gap-2 mb-3">
                     <input className="input-admin" placeholder="Nome" value={newCityName} onChange={e => setNewCityName(e.target.value)} />
                     <input className="input-admin w-24" placeholder="Lat" value={newCityLat} onChange={e => setNewCityLat(e.target.value)} />
                     <input className="input-admin w-24" placeholder="Lng" value={newCityLng} onChange={e => setNewCityLng(e.target.value)} />
                     <button className="btn-blue" onClick={() => handleGeocode(newCityName, null, setCitySuggestions, setLoadingCityGeo, setCityMsg)}>{loadingCityGeo ? "..." : "Buscar GPS"}</button>
                     <button className="btn-save" onClick={handleCreateCity}>Salvar</button>
                   </div>
                   {citySuggestions.length > 0 && (<div className="bg-slate-800 p-2 rounded mb-2 text-xs">{citySuggestions.map((s, i) => <div key={i} onClick={() => { setNewCityLat(String(s.latitude)); setNewCityLng(String(s.longitude)); setCitySuggestions([]) }} className="cursor-pointer hover:text-emerald-400 p-1">{s.display_name}</div>)}</div>)}
                   
                   {/* Filtro Cidades */}
                   <input className="input-admin w-full mb-2 text-sm bg-slate-800" placeholder="🔍 Filtrar cidades..." value={filterCity} onChange={e => setFilterCity(e.target.value)} />
                   
                   <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                     {cities.filter(c => c.name.toLowerCase().includes(filterCity.toLowerCase())).map(c => (<span key={c.id} className="tag-item">{c.name} <button onClick={() => handleDeleteCity(c.id)} className="text-red-400 ml-1">x</button></span>))}
                   </div>
                 </div>

                 {/* 3. BAIRROS */}
                 <div className="mb-6 pb-6 border-b border-slate-800">
                    <h3 className="text-emerald-400 font-bold mb-2">3. Bairros (Opcional)</h3>
                    <div className="flex flex-wrap gap-2 mb-3">
                      <select className="input-admin" value={nbCityId} onChange={e => setNbCityId(e.target.value)}><option value="">Cidade...</option>{cities.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
                      <input className="input-admin" placeholder="Nome Bairro" value={nbName} onChange={e => setNbName(e.target.value)} />
                      <input className="input-admin w-24" placeholder="Lat" value={nbLat} onChange={e => setNbLat(e.target.value)} />
                      <input className="input-admin w-24" placeholder="Lng" value={nbLng} onChange={e => setNbLng(e.target.value)} />
                      <button className="btn-blue" onClick={() => handleGeocode(nbName, nbCityId, setNbSuggestions, setNbLoading, setNbMsg)}>{nbLoading ? "..." : "Buscar GPS"}</button>
                      <button className="btn-save" onClick={handleCreateNeighborhood}>Salvar</button>
                    </div>
                    {nbSuggestions.length > 0 && (<div className="bg-slate-800 p-2 rounded mb-2 text-xs">{nbSuggestions.map((s, i) => <div key={i} onClick={() => { setNbLat(String(s.latitude)); setNbLng(String(s.longitude)); setNbSuggestions([]) }} className="cursor-pointer hover:text-emerald-400 p-1">{s.display_name}</div>)}</div>)}
                    
                    {/* Filtro Bairros */}
                    <input className="input-admin w-full mb-2 text-sm bg-slate-800" placeholder="🔍 Filtrar bairros..." value={filterNb} onChange={e => setFilterNb(e.target.value)} />

                    <div className="space-y-1 max-h-32 overflow-y-auto">
                      {neighborhoods.filter(nb => nb.name.toLowerCase().includes(filterNb.toLowerCase()) || getCityName(nb.city_id).toLowerCase().includes(filterNb.toLowerCase())).map(nb => (
                        <div key={nb.id} className="flex justify-between items-center bg-slate-800 p-1 px-2 rounded text-xs">
                          <span>{getCityName(nb.city_id)} - {nb.name}</span>
                          <button onClick={() => handleDeleteNeighborhood(nb.id)} className="text-red-400 font-bold ml-2">x</button>
                        </div>
                      ))}
                    </div>
                 </div>

                 {/* 4. VEÍCULOS */}
                 <div className="mb-6 pb-6 border-b border-slate-800">
                   <h3 className="text-emerald-400 font-bold mb-2">4. Veículos</h3>
                   <div className="flex flex-wrap gap-2 mb-3"><input className="input-admin" placeholder="Nome" value={newVehicleName} onChange={e => setNewVehicleName(e.target.value)} /><input className="input-admin w-32" placeholder="Placa" value={newVehiclePlate} onChange={e => setNewVehiclePlate(e.target.value)} /><button className="btn-save" onClick={handleCreateVehicle}>Salvar</button></div>
                   
                   {/* Filtro Veículos */}
                   <input className="input-admin w-full mb-2 text-sm bg-slate-800" placeholder="🔍 Filtrar veículos..." value={filterVehicle} onChange={e => setFilterVehicle(e.target.value)} />

                   <div className="flex flex-wrap gap-2 max-h-32 overflow-y-auto">
                     {vehicles.filter(v => v.name.toLowerCase().includes(filterVehicle.toLowerCase())).map(v => (<span key={v.id} className="tag-item">{v.name} <button onClick={() => handleDeleteVehicle(v.id)} className="text-red-400 ml-1">x</button></span>))}
                   </div>
                 </div>

                 {/* 5. VÍNCULOS */}
                 <div>
                   <h3 className="text-emerald-400 font-bold mb-2">5. Vincular Logística</h3>
                   <div className="flex flex-wrap gap-2 mb-4 bg-slate-800 p-3 rounded-lg">
                     <select className="input-admin" value={linkRouteId} onChange={e => setLinkRouteId(e.target.value)}><option value="">1. Rota...</option>{routes.map(r => <option key={r.id} value={r.id}>{r.name}</option>)}</select>
                     <select className="input-admin" value={linkCityId} onChange={e => { setLinkCityId(e.target.value); setLinkNeighborhoodId(""); }}><option value="">2. Cidade...</option>{cities.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}</select>
                     <select className="input-admin" value={linkNeighborhoodId} onChange={e => setLinkNeighborhoodId(e.target.value)}><option value="">3. Bairro...</option>{neighborhoods.filter(n => n.city_id === Number(linkCityId)).map(n => <option key={n.id} value={n.id}>{n.name}</option>)}</select>
                     <select className="input-admin" value={linkWeekday} onChange={e => setLinkWeekday(e.target.value)}><option value="">4. Dia...</option><option value="7">Todos os dias</option>{Object.entries(WEEKDAYS).filter(([k]) => k !== '7').map(([k,v]) => <option key={k} value={k}>{v}</option>)}</select>
                     <select className="input-admin" value={linkVehicleId} onChange={e => setLinkVehicleId(e.target.value)}><option value="">5. Veículo...</option>{vehicles.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}</select>
                     <button className="btn-save w-full md:w-auto" onClick={handleLinkRouteCityDay}>CRIAR VÍNCULO</button>
                   </div>
                   
                   {/* Filtro Vínculos */}
                   <input className="input-admin w-full mb-2 text-sm bg-slate-800" placeholder="🔍 Filtrar vínculos (cidade, rota, dia)..." value={filterLink} onChange={e => setFilterLink(e.target.value)} />

                   <div className="max-h-60 overflow-y-auto space-y-1 text-sm bg-slate-950 p-2 rounded border border-slate-800">
                      {links.filter(l => {
                          const term = filterLink.toLowerCase();
                          return getRouteName(l.route_id).toLowerCase().includes(term) ||
                                 getCityName(l.city_id).toLowerCase().includes(term) ||
                                 (l.neighborhood_id && getNeighborhoodName(l.neighborhood_id).toLowerCase().includes(term));
                      }).map(l => (<div key={l.id} className="flex justify-between items-center p-2 hover:bg-slate-900 rounded border-b border-slate-900"><span><span className="text-emerald-400 font-bold">{getRouteName(l.route_id)}</span> ➔ {getCityName(l.city_id)} {l.neighborhood_id && `(${getNeighborhoodName(l.neighborhood_id)})`} <span className="text-slate-500 ml-2 text-xs">[{WEEKDAYS[l.weekday]}]</span></span><button onClick={() => handleDeleteLink(l.id)} className="text-xs bg-red-900 text-red-200 px-2 py-1 rounded hover:bg-red-800">Remover</button></div>))}
                   </div>
                 </div>
              </div>
            </div>
          )
        )}
      </div>
      <style>{`
        .input-admin { background: #0f172a; border: 1px solid #334155; padding: 6px 10px; border-radius: 6px; color: white; outline: none; } .input-admin:focus { border-color: #10b981; }
        .btn-save { background: #10b981; color: #020617; font-weight: bold; padding: 6px 12px; border-radius: 6px; } .btn-save:hover { background: #059669; }
        .btn-blue { background: #3b82f6; color: white; padding: 6px 12px; border-radius: 6px; font-size: 0.8rem; } .btn-blue:hover { background: #2563eb; }
        .tag-item { background: #1e293b; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem; border: 1px solid #334155; }
      `}</style>
    </div>
  );
}

export default App;