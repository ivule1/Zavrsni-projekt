import { CHART_PALETTE } from "../chartPalette";

// Stupicasti graf - poput DonutChart-a, bez vanjske dataviz biblioteke
// (cist SVG/CSS), ali kao SAMOSTALAN graf (ne kao rasklopivi popis kakav je
// BreakdownList) - za mjesta gdje sama vizualizacija treba biti glavni
// prikaz, a ne sporedna traka uz naslov retka koji se rasklapa.
//
// orientation="vertical" (zadano) - stupci jedan pored drugog, s
// razmakom medju njima, umjesto vodoravnih traka poredanih jedna ispod
// druge. Kad ovaj graf stoji NEPOSREDNO IZNAD popisa (npr. BreakdownList
// showDetails=false) koji je isto niz vodoravnih traka, dvije vizualno
// identicne "trake" komponente spojene jedna na drugu djeluju kao JEDAN
// dugacak, nepregledan popis - okomiti stupci su vizualno jasno odvojeni
// (drukciji oblik) pa se odmah vidi gdje graf zavrsava i popis pocinje.
// orientation="horizontal" - staro ponasanje (vodoravne trake, jedna ispod
// druge), zadrzano za slucaj da ikad ustreba.
//
// mode="value" (zadano) - visina/duljina stupca RELATIVNA je prema
// najvecoj vrijednosti u skupu (dobro za usporedbu apsolutnih brojeva).
// mode="percent" - svaki stupac nosi svoju vec izracunatu, NEOVISNU 0-100%
// vrijednost (dobro za izlaznost, gdje svaka skupina ima drugaciji broj
// upisanih biraca pa usporedba "prema najvecoj skupini" ne bi imala smisla).
//
// showLabels=false - ne ispisuje naziv ispod svakog stupca (koristi se kad
// graf stoji odmah pored DonutChart-a koji vec ima svoju legendu s istim
// bojama/nazivima/brojkama - dupliciranje bi samo zauzelo prostor bez nove
// informacije, boja stupca vec govori na kojeg se kandidata odnosi).
// scrollable=true (samo orientation="vertical") - kad ima puno stupaca
// (npr. ~20 zupanija), umjesto stiskanja svih u raspoloziva sirinu, stupci
// dobivaju fiksnu sirinu i cijeli graf postaje vodoravno skrolabilan - tako
// svaki stupac i njegov naziv ostaju citljivi bez obzira na broj skupina.
export default function BarChart({
  data,
  mode = "value",
  formatValue,
  maxHeight,
  orientation = "vertical",
  showLabels = true,
  scrollable = false,
  height = 150,
}) {
  const maxValue = mode === "percent" ? 100 : Math.max(1, ...data.map((d) => d.value));

  if (orientation === "vertical") {
    return (
      <div
        className={`bar-chart bar-chart--vertical${scrollable ? " bar-chart--scrollable" : ""}`}
        style={maxHeight ? { maxHeight, overflowY: "auto" } : undefined}
      >
        {data.length === 0 && <p className="text-muted small mb-0">Nema podataka.</p>}
        {data.map((d, i) => {
          const pct = mode === "percent" ? Math.max(0, Math.min(100, d.value)) : (d.value / maxValue) * 100;
          const color = d.color || CHART_PALETTE[i % CHART_PALETTE.length];
          return (
            <div className="bar-chart-col" key={d.label} title={d.label}>
              <span className="bar-chart-col-value">{formatValue ? formatValue(d) : d.value}</span>
              <div className="bar-chart-col-track" style={{ height }}>
                <div className="bar-chart-col-fill" style={{ height: `${pct}%`, backgroundColor: color }} />
              </div>
              {showLabels && <span className="bar-chart-col-label">{d.label}</span>}
            </div>
          );
        })}
      </div>
    );
  }

  return (
    <div className="bar-chart" style={maxHeight ? { maxHeight, overflowY: "auto" } : undefined}>
      {data.length === 0 && <p className="text-muted small mb-0">Nema podataka.</p>}
      {data.map((d, i) => {
        const pct = mode === "percent" ? Math.max(0, Math.min(100, d.value)) : (d.value / maxValue) * 100;
        return (
          <div className="bar-chart-row" key={d.label}>
            {showLabels && <span className="bar-chart-label">{d.label}</span>}
            <span className="bar-chart-track">
              <span
                className="bar-chart-fill"
                style={{ width: `${pct}%`, backgroundColor: d.color || CHART_PALETTE[i % CHART_PALETTE.length] }}
              />
            </span>
            <span className="bar-chart-value">{formatValue ? formatValue(d) : d.value}</span>
          </div>
        );
      })}
    </div>
  );
}
