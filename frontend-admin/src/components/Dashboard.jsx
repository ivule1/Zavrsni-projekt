import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError, WS_BASE_URL, getVoteCounts, listElections } from "../api";
import AdminWatermark from "./AdminWatermark";
import DevicesTokensTab from "./DevicesTokensTab";
import ElectionsTab from "./ElectionsTab";
import MonitorTab from "./MonitorTab";
import StationsTab from "./StationsTab";

const TABS = [
  { id: "nadzor", label: "Nadzor" },
  { id: "izbori", label: "Izbori i kandidati" },
  { id: "biralista", label: "Biračka mjesta" },
  { id: "uredjaji", label: "Uređaji i tokeni" },
];

export default function Dashboard({ token, onLogout }) {
  const [activeTab, setActiveTab] = useState("nadzor");
  const [elections, setElections] = useState([]);
  const [selectedElectionId, setSelectedElectionId] = useState("");
  const [voteCounts, setVoteCounts] = useState(null);
  const [flashStation, setFlashStation] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [loadError, setLoadError] = useState("");
  const wsRef = useRef(null);
  // WS veza se otvara JEDNOM i ostaje otvorena dok admin mijenja odabrani
  // izbor u padajucem izborniku - zato "trenutno odabrani izbor" drzimo i u
  // refu (uz useState), da ga onmessage handler unutar efekta uvijek cita
  // svjeze, a ne "zamrznutu" vrijednost iz trenutka kad je efekt pokrenut.
  const selectedElectionIdRef = useRef(selectedElectionId);
  useEffect(() => {
    selectedElectionIdRef.current = selectedElectionId;
  }, [selectedElectionId]);

  const selectedElection = elections.find((e) => e.id === selectedElectionId) || null;

  const reloadElections = useCallback(() => {
    return listElections(token)
      .then((data) => {
        setElections(data);
        setSelectedElectionId((prev) => prev || data[0]?.id || "");
        return data;
      })
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Greška pri učitavanju izbora."));
  }, [token]);

  // Popis izbora - ucita se jednom nakon prijave (i ponovno na zahtjev iz
  // Izbori taba, npr. nakon kreiranja/otvaranja/zatvaranja izbora)
  useEffect(() => {
    reloadElections();
  }, [reloadElections]);

  const loadVoteCounts = useCallback(() => {
    if (!selectedElectionId) return;
    getVoteCounts(token, selectedElectionId)
      .then(setVoteCounts)
      .catch((err) => setLoadError(err instanceof ApiError ? err.message : "Greška pri učitavanju broja glasova."));
  }, [token, selectedElectionId]);

  // Pocetno stanje (prije nego WS eventi pocnu stizati) - poglavlje 16.
  // Namjerno NE resetiramo voteCounts na null prije novog fetcha (kratki
  // "flash" starih podataka je prihvatljiv, a izbjegava se sinkroni
  // setState odmah na pocetku efekta).
  useEffect(() => {
    loadVoteCounts();
  }, [loadVoteCounts]);

  // WebSocket - poglavlje 14/34.3: spoji se JEDNOM (dok je admin prijavljen),
  // posalji JWT kao prvu poruku, pa primaj real-time vote_count evente.
  // Filtriramo po trenutno odabranom izboru na klijentu. Drzi se ovdje (u
  // Dashboardu), ne u MonitorTabu, da veza ne puca kad admin prebaci karticu.
  useEffect(() => {
    const ws = new WebSocket(`${WS_BASE_URL}/ws/admin`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ token }));
    };

    ws.onmessage = (event) => {
      if (event.data === "ping") return;
      let msg;
      try {
        msg = JSON.parse(event.data);
      } catch {
        return;
      }

      if (msg.type === "connected") {
        setWsConnected(true);
        return;
      }

      if (msg.type === "vote_count") {
        if (msg.election_id !== selectedElectionIdRef.current) return;
        setVoteCounts((prev) => {
          if (!prev) return prev;
          const stations = prev.stations.map((s) =>
            s.station_id === msg.station_id ? { ...s, count: msg.count } : s,
          );
          const total = stations.reduce((sum, s) => sum + s.count, 0);
          return { ...prev, stations, total_votes: total };
        });
        setFlashStation(msg.station_id);
        setTimeout(() => setFlashStation(null), 1000);
        return;
      }

      if (msg.type === "election_changed") {
        // Izbor je kreiran/otvoren/zatvoren - moguce na drugom mjestu (npr.
        // kroz Swagger, ili u drugoj kartici admin konzole) dok je ovaj
        // dashboard vec otvoren. Popis izbora se inace dohvaca samo
        // jednom pri prijavi, pa bez ovoga admin ne bi vidio promjenu bez
        // rucnog osvjezavanja stranice.
        reloadElections();
      }
    };

    ws.onclose = () => setWsConnected(false);
    ws.onerror = () => setWsConnected(false);

    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  return (
    <div className="admin-shell">
      <div className="admin-header">
        <div className="admin-header-title-group">
          <AdminWatermark inline />
          <h1 className="admin-title">E-Glasanje - Admin konzola</h1>
        </div>
        <div className="d-flex align-items-center gap-3">
          <span className={`ws-indicator ${wsConnected ? "connected" : "disconnected"}`}>
            <span className="ws-dot" />
            {wsConnected ? "Nadzor uživo aktivan" : "Nadzor uživo prekinut"}
          </span>
          <button type="button" className="btn btn-outline-secondary btn-sm" onClick={onLogout}>
            Odjava
          </button>
        </div>
      </div>

      <div className="admin-tabs">
        {TABS.map((tab) => (
          <button
            key={tab.id}
            type="button"
            className={`admin-tab ${activeTab === tab.id ? "active" : ""}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {loadError && <div className="alert alert-danger">{loadError}</div>}

      {activeTab === "nadzor" && (
        <MonitorTab
          token={token}
          elections={elections}
          selectedElectionId={selectedElectionId}
          setSelectedElectionId={setSelectedElectionId}
          selectedElection={selectedElection}
          voteCounts={voteCounts}
          flashStation={flashStation}
        />
      )}

      {activeTab === "izbori" && (
        <ElectionsTab token={token} elections={elections} onElectionsChanged={reloadElections} />
      )}

      {activeTab === "biralista" && <StationsTab token={token} />}

      {activeTab === "uredjaji" && <DevicesTokensTab token={token} />}
    </div>
  );
}
