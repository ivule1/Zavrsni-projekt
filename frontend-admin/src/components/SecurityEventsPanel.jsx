import { useEffect, useState } from "react";
import { ApiError, getAuditLogs } from "../api";

// FAZA 9 (dopuna) - poglavlje 16: "Administrator ima pristup... system
// events, security events." Do sada je admin dashboard pokrivao election
// status/stanice/uredjaje/broj glasova/izlaznost/tally, ali NIJE imao nikakav
// prikaz sigurnosnih/sistemskih dogadaja iz audit_logs (poglavlje 22) - ova
// kartica je taj nedostajuci dio.
//
// Namjerno REST + "Osvjezi" gumb (isti obrazac kao DeviceVoteCounts), ne
// WebSocket - vidi opsirno obrazlozenje u app/audit/router.py na backendu
// (log_event() namjerno ne commita ni ne emitira WS event sam za sebe, pa bi
// generickо emitiranje odavde moglo prijeviti prije stvarnog commita,
// poglavlje 15/RULE 08).
//
// Sigurnosno bitno: metadata polje koje backend vraca je vec zajamceno
// bezopasno (poglavlje 22-23, provjereno u app/audit/service.py i na svim
// mjestima koja pozivaju log_event) - ova komponenta ga samo ispisuje kao
// JSON, ne dodaje nikakvu novu izlozenost.

const EVENT_LABELS = {
  ADMIN_LOGIN: "Prijava administratora",
  ELECTION_CREATED: "Izbor kreiran",
  ELECTION_OPENED: "Izbor otvoren",
  ELECTION_CLOSED: "Izbor zatvoren",
  CANDIDATE_ADDED: "Kandidat dodan",
  STATION_REGISTERED: "Biralište registrirano",
  STATIONS_BULK_IMPORTED: "Biračka mjesta uvezena (bulk)",
  DEVICE_REGISTERED: "Uređaj registriran",
  TOKEN_POOL_GENERATED: "Generiran skup tokena",
  TOKEN_VALIDATION_SUCCESS: "Token uspješno validiran",
  INVALID_TOKEN_ATTEMPT: "Pokušaj s nepostojećim tokenom",
  TOKEN_ALREADY_USED_ATTEMPT: "Pokušaj ponovne uporabe tokena",
  VOTE_ACCEPTED: "Glas zaprimljen",
  TALLY_PERFORMED: "Brojanje glasova izvršeno",
};

// Dogadaji koji signaliziraju pokusaj zaobilazenja sustava (RULE 05/06) -
// vizualno istaknuti (isti stil kao integrity-bad/tally-warning) da ih admin
// odmah uoci umjesto da se izgube medju rutinskim dogadajima.
const SUSPICIOUS_EVENTS = new Set(["INVALID_TOKEN_ATTEMPT", "TOKEN_ALREADY_USED_ATTEMPT"]);

function eventLabel(type) {
  return EVENT_LABELS[type] || type;
}

function formatTime(iso) {
  return new Date(iso).toLocaleString("hr-HR");
}

export default function SecurityEventsPanel({ token }) {
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const load = () => {
    setLoading(true);
    setError("");
    getAuditLogs(token, { limit: 50 })
      .then(setData)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Greška pri učitavanju dogadaja."))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <details className="admin-card collapsible-card">
      <summary>
        <span className="h5 mb-0">Sigurnosni i sistemski događaji</span>
        <span className="d-flex align-items-center gap-2">
          {data && <span className="text-muted small">Zadnjih {data.items.length}</span>}
          <button
            type="button"
            className="btn btn-outline-secondary btn-sm"
            onClick={(e) => {
              e.preventDefault();
              load();
            }}
            disabled={loading}
          >
            {loading ? "Osvježavam..." : "Osvježi"}
          </button>
        </span>
      </summary>

      <div className="collapsible-card-body">
        <p className="text-muted small mb-3">
          Zapisi iz audit loga (poglavlje 22) - prijave, promjene statusa izbora, registracije, pokušaji s
          nevažećim/iskorištenim tokenom i sl. Nikad ne sadrži identitet birača, sirovi ključ ni vezu ključ→glas.
        </p>
        {error && <div className="alert alert-danger py-2">{error}</div>}

        {data && (
          <div className="audit-log-list">
            {data.items.map((item) => (
              <div key={item.id} className={`audit-log-row${SUSPICIOUS_EVENTS.has(item.event_type) ? " audit-log-row--suspicious" : ""}`}>
                <span className="audit-log-time">{formatTime(item.created_at)}</span>
                <span className="audit-log-type">{eventLabel(item.event_type)}</span>
                <span className="audit-log-context">
                  {item.station_code && <span>{item.station_code}</span>}
                  {item.admin_username && <span>{item.admin_username}</span>}
                  {item.metadata && (
                    <span className="audit-log-meta">
                      {Object.entries(item.metadata)
                        .map(([k, v]) => `${k}: ${v}`)
                        .join(", ")}
                    </span>
                  )}
                </span>
              </div>
            ))}
            {data.items.length === 0 && <p className="text-muted small mb-0">Nema zabilježenih događaja.</p>}
            {data.has_more && <p className="text-muted small mb-0 mt-2">Prikazano zadnjih {data.items.length} - stariji zapisi postoje.</p>}
          </div>
        )}
      </div>
    </details>
  );
}
