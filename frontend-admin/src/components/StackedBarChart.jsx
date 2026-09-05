// Slozeni ("stacked") stupicasti graf s osi - svaki stupac je sastavljen od
// vise segmenata (jedan segment = jedan kandidat, ISTA boja kao u "Rezultati
// po kandidatu" - vidi candidateColorById u TallyPanelu), tako da VISINA
// stupca prikazuje ukupan broj glasova (izlaznost) u toj skupini (biraliste/
// zupanija/regija), a RAZDIOBA BOJA UNUTAR stupca prikazuje kako su se ti
// glasovi podijelili po kandidatu - jedan graf, dvije informacije odjednom,
// umjesto da "Rezultati po..." zapravo pokazuju samo ukupan broj (sto je
// izlaznost, ne rezultat).
//
// Os s brojevima sa strane (linije + oznake) - "niceMax" zaokruzuje
// najvecu vrijednost na okrugao broj (npr. 56 -> 60) i dijeli je na 4
// jednaka dijela za 5 crta (0, 1/4, 1/2, 3/4, max) - isto kao standardni
// dashboard grafovi, da se vrijednost moze procijeniti i bez gledanja
// tocnog broja iznad stupca.
function niceMax(value) {
  if (value <= 0) return 1;
  const magnitude = Math.pow(10, Math.floor(Math.log10(value)));
  const residual = value / magnitude;
  let niceResidual;
  if (residual > 5) niceResidual = 10;
  else if (residual > 2) niceResidual = 5;
  else if (residual > 1) niceResidual = 2;
  else niceResidual = 1;
  return niceResidual * magnitude;
}

// data: [{ label, total, segments: [{ name, value, color }] }]
// Ocekuje se da je `data` VEC poredan onako kako pozivatelj zeli (TallyPanel
// sortira po total, opadajuce) - ova komponenta samo iscrtava zadani
// redoslijed, ne sortira sama.
export default function StackedBarChart({ data, height = 190, scrollable = false }) {
  const maxTotal = Math.max(1, ...data.map((d) => d.total));
  const axisMax = niceMax(maxTotal);
  const ticks = [0, axisMax / 4, axisMax / 2, (axisMax * 3) / 4, axisMax];
  const scrollableClass = scrollable ? " is-scrollable" : "";

  if (data.length === 0) {
    return <p className="text-muted small mb-0">Nema podataka.</p>;
  }

  return (
    <div className={`stacked-bar-chart-scroll${scrollableClass}`}>
      <div className="stacked-bar-chart-plot" style={{ height }}>
        {ticks.map((t) => (
          <div key={t} className="stacked-bar-chart-gridline" style={{ bottom: `${(t / axisMax) * 100}%` }}>
            <span className="stacked-bar-chart-tick-label">{Math.round(t)}</span>
          </div>
        ))}
        <div className={`stacked-bar-chart-tracks${scrollableClass}`}>
          {data.map((d) => (
            <div className={`stacked-bar-chart-col${scrollableClass}`} key={d.label}>
              <div className="stacked-bar-chart-col-track" title={d.label}>
                {d.segments
                  .filter((s) => s.value > 0)
                  .map((s) => (
                    <div
                      key={s.name}
                      className="stacked-bar-chart-segment"
                      style={{ height: `${(s.value / axisMax) * 100}%`, backgroundColor: s.color }}
                      title={`${s.name}: ${s.value}`}
                    />
                  ))}
                <span
                  className="stacked-bar-chart-col-value"
                  style={{ bottom: `${(d.total / axisMax) * 100}%` }}
                >
                  {d.total}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
      <div className={`stacked-bar-chart-labels${scrollableClass}`}>
        {data.map((d) => (
          <span className={`stacked-bar-chart-col-label${scrollableClass}`} key={d.label} title={d.label}>
            {d.label}
          </span>
        ))}
      </div>
    </div>
  );
}
