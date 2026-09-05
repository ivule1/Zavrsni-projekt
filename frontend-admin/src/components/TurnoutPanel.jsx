import { useEffect, useState } from "react";
import { ApiError, listStations } from "../api";
import { CHART_PALETTE } from "../chartPalette";
import BarChart from "./BarChart";
import BreakdownList from "./BreakdownList";

// FAZA 9 (dopuna, zadatak #19) - izlaznost po zupaniji/regiji UZIVO, dok je
// izbor jos OTVOREN (prije brojanja/Tally-ja). Namjerno ne trazi nista novo
// od backenda: spaja vec-zivi voteCounts.stations (isti WS podaci koji vec
// azuriraju "Glasovi po biralistu" u MonitorTabu) sa statickim podacima o
// biralistima (zupanija/regija/registered_voters) dohvacenim jednom preko
// GET /stations. Time je "live preko WS" rijeseno besplatno - ovo je samo
// izvedeni prikaz nad vec-zivim stanjem, bez ikakvog dodatnog WS kanala.
//
// SIGURNOSNO OGRANICENJE (poglavlje 34.1, RULE 01-12): dok je izbor OTVOREN,
// glasovi se ne mogu dekriptirati, pa razdioba po KANDIDATU ne postoji i ne
// smije postojati u ovom prikazu - zato se ovdje racunaju i prikazuju SAMO
// zbrojevi glasova i postotci izlaznosti po grupi, nikad po kandidatu.
// BreakdownList se zato zove s showDetails={false}, sto znaci da komponenta
// uopce ne poziva getByCandidate - nema mehanizma kojim bi ta podjela ovdje
// procurila.

function buildGroups(voteCounts, stationsById, keyFn) {
  const groups = new Map();
  for (const s of voteCounts.stations) {
    const meta = stationsById.get(s.station_id);
    const key = (meta && keyFn(meta)) || "Nepoznato";
    const existing = groups.get(key) || { group: key, total: 0, registered: 0 };
    existing.total += s.count;
    existing.registered += meta ? meta.registered_voters : 0;
    groups.set(key, existing);
  }
  return Array.from(groups.values()).sort((a, b) => b.total - a.total);
}

function turnoutLabel(g) {
  if (!g.registered) return `${g.total} glasova`;
  const pct = ((g.total / g.registered) * 100).toFixed(1);
  return `${g.total} / ${g.registered} (${pct}%)`;
}

// Podaci za BarChart mode="percent" - izlaznost svake skupine RACUNA SE
// NEOVISNO o ostalima (glasovi/upisani birači te skupine), za razliku od
// stupca u BreakdownList-u koji je (namjerno, za drugu svrhu) proporcionalan
// prema NAJVECOJ skupini po broju glasova. Kruzni graf (pie/donut) je ovdje
// namjerno izbjegnut - s vrlo razlicitim brojem upisanih biraca po skupini
// (npr. Dijaspora ima samo 300 nasuprot ~18000 za veliku regiju), tortni
// graf udjela GLASOVA ne govori nista o IZLAZNOSTI, a "Dijaspora" kao
// jedna kriska torte medju "pravim" NUTS2 regijama djeluje zbunjujuce -
// stupicasti prikaz s neovisnom 0-100% skalom po retku to rjesava.
function turnoutPercentData(groups) {
  return groups.map((g, i) => ({
    label: g.group,
    value: g.registered ? (g.total / g.registered) * 100 : 0,
    color: CHART_PALETTE[i % CHART_PALETTE.length],
  }));
}

export default function TurnoutPanel({ token, voteCounts }) {
  const [stations, setStations] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    listStations(token)
      .then(setStations)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Greška pri učitavanju biračkih mjesta."));
  }, [token]);

  if (error) {
    return (
      <div className="admin-card">
        <h2 className="h5 mb-3">Izlaznost uživo</h2>
        <div className="alert alert-danger py-2 mb-0">{error}</div>
      </div>
    );
  }

  if (!stations || !voteCounts) {
    return (
      <div className="admin-card">
        <h2 className="h5 mb-3">Izlaznost uživo</h2>
        <p className="text-muted mb-0">Učitavam...</p>
      </div>
    );
  }

  const stationsById = new Map(stations.map((s) => [s.id, s]));
  const byRegion = buildGroups(voteCounts, stationsById, (m) => m.region || "Nepoznato");
  const byZupanija = buildGroups(voteCounts, stationsById, (m) => m.zupanija || "Nepoznato");

  const totalRegistered = stations.reduce((sum, s) => sum + s.registered_voters, 0);
  const totalPct = totalRegistered ? ((voteCounts.total_votes / totalRegistered) * 100).toFixed(1) : null;

  return (
    <div className="admin-card">
      <div className="d-flex justify-content-between align-items-center mb-2 flex-wrap gap-2">
        <h2 className="h5 mb-0">Izlaznost uživo</h2>
        <span>
          Ukupno: <strong>{voteCounts.total_votes}</strong>
          {totalPct !== null && (
            <span className="text-muted">
              {" "}
              / {totalRegistered} ({totalPct}%)
            </span>
          )}
        </span>
      </div>
      <p className="text-muted small mb-3">
        Prikaz dok je izbor otvoren - samo ukupni broj glasova i izlaznost po skupini. Razdioba po kandidatu
        nije dostupna prije zatvaranja izbora i brojanja (poglavlje 34.1). Broj upisanih birača
        (registered_voters) je za sada jednaka placeholder vrijednost (300) za svako biralište, pa je postotak
        izlaznosti okviran, ne stvaran.
      </p>

      <h3 className="h6 mt-3 mb-3">Izlaznost po NUTS2 regiji</h3>
      <BarChart mode="percent" data={turnoutPercentData(byRegion)} formatValue={(d) => `${d.value.toFixed(1)}%`} />
      <BreakdownList
        groups={byRegion}
        getKey={(g) => g.group}
        getLabel={(g) => g.group}
        getTotal={(g) => g.total}
        getSubLabel={turnoutLabel}
        showDetails={false}
      />

      <h3 className="h6 mt-4 mb-3">Izlaznost po županiji</h3>
      <BarChart
        mode="percent"
        scrollable
        data={turnoutPercentData(byZupanija)}
        formatValue={(d) => `${d.value.toFixed(1)}%`}
      />
      <BreakdownList
        groups={byZupanija}
        getKey={(g) => g.group}
        getLabel={(g) => g.group}
        getTotal={(g) => g.total}
        getSubLabel={turnoutLabel}
        showDetails={false}
        maxHeight="40vh"
      />
    </div>
  );
}
