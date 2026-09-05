import { useCallback, useEffect, useRef, useState } from "react";
import CandidateSelectScreen from "./components/CandidateSelectScreen";
import ConfirmScreen from "./components/ConfirmScreen";
import ErrorScreen from "./components/ErrorScreen";
import KioskHeader from "./components/KioskHeader";
import SuccessScreen from "./components/SuccessScreen";
import TokenEntryScreen from "./components/TokenEntryScreen";
import { ApiError, WS_BASE_URL, castVote, getCurrentElection, validateToken } from "./api";

// Poglavlje 12 - tok kabine: unos kljuca -> validacija -> izbor kandidata -> potvrda -> zaprimljeno
const STEP = {
  TOKEN: "token",
  CANDIDATES: "candidates",
  CONFIRM: "confirm",
  SUCCESS: "success",
  ERROR: "error",
};

// Kiosk mora sam resetirati sesiju - birac ne smije naslijediti tudji napola
// zavrsen proces, niti terminal smije ostati "zaglavljen" na necijem izboru.
const IDLE_RESET_MS = 90_000;
const SUCCESS_DISPLAY_MS = 6_000;

const ERROR_MESSAGES = {
  INVALID_TOKEN: "Uneseni ključ ne postoji. Provjerite je li ispravno upisan.",
  TOKEN_ALREADY_USED: "Ovaj ključ je već iskorišten.",
  ELECTION_NOT_OPEN: "Glasanje trenutno nije otvoreno.",
  DEVICE_NOT_AUTHORIZED: "Terminal nije autoriziran. Pozovite službenika.",
  CANDIDATE_NOT_FOUND: "Odabrani kandidat više nije dostupan. Pokušajte ponovno.",
  DATABASE_ERROR: "Sustav trenutno nije dostupan. Pozovite službenika.",
  SERVER_ERROR: "Došlo je do neočekivane greške. Pozovite službenika.",
  NETWORK_ERROR: "Nije moguće spojiti se na sustav. Pozovite službenika.",
};

function translateError(code) {
  return ERROR_MESSAGES[code] || "Došlo je do greške. Pozovite službenika.";
}

// Sirovi dohvat trenutnog izbora (bez postavljanja state-a) - koristi se i
// pri pokretanju terminala i ponovno pri svakom unosu kljuca (vidi
// handleTokenSubmit). Terminal moze ostati otvoren dulje vrijeme (kiosk),
// pa se izbor moze otvoriti TEK NAKON sto je stranica vec ucitana - ako
// bismo se oslanjali samo na podatke iz trenutka pokretanja, birac bi
// dobio pogresnu poruku "izbor nije otvoren" iako je u bazi vec otvoren.
// Vraca null ako dohvat nije uspio (izbor nije otvoren / terminal nije
// autoriziran) - pozivatelj tada samo tiho ne popunjava zaglavlje.
async function fetchCurrentElection() {
  try {
    return await getCurrentElection();
  } catch {
    return null;
  }
}

export default function App() {
  const [step, setStep] = useState(STEP.TOKEN);
  const [loading, setLoading] = useState(false);
  const [token, setToken] = useState("");
  const [electionName, setElectionName] = useState("");
  const [candidates, setCandidates] = useState([]);
  const [selectedCandidate, setSelectedCandidate] = useState(null);
  const [errorMessage, setErrorMessage] = useState("");
  const idleTimerRef = useRef(null);

  // Terminal ucita naziv izbora i kandidate odmah pri pokretanju (device
  // kljuc je dovoljan, ne treba glasacki token) - da se zaglavlje i popis
  // kandidata prikazu bez cekanja na svakog pojedinog biraca.
  useEffect(() => {
    let cancelled = false;
    fetchCurrentElection().then((election) => {
      if (!cancelled && election) {
        setElectionName(election.election_name);
        setCandidates(election.candidates);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  // FAZA 9 (bonus) - javni WS kanal (bez autentikacije - vidi backend
  // /ws/status) koji terminalu samo "gurne" signal kad se neki izbor
  // otvori/zatvori/kreira, pa zaglavlje ne mora cekati da prvi birac unese
  // kljuc. WS ovdje NIKAD nije jedini izvor istine (poglavlje 15 princip) -
  // ako veza uopce ne uspije ili padne, terminal i dalje radi ispravno
  // (fetchCurrentElection se svejedno ponovno zove pri unosu kljuca), pa se
  // ovdje nista ne prijavljuje biracu ni pri neuspjehu ni pri prekidu.
  useEffect(() => {
    let cancelled = false;
    let socket = null;
    let reconnectTimer = null;

    const connect = () => {
      if (cancelled) return;
      socket = new WebSocket(`${WS_BASE_URL}/ws/status`);

      socket.onmessage = (event) => {
        if (event.data === "ping" || event.data === "pong") return;
        let msg;
        try {
          msg = JSON.parse(event.data);
        } catch {
          return;
        }
        if (msg.type === "election_changed") {
          fetchCurrentElection().then((election) => {
            if (!cancelled && election) {
              setElectionName(election.election_name);
              setCandidates(election.candidates);
            }
          });
        }
      };

      socket.onclose = () => {
        if (!cancelled) {
          reconnectTimer = setTimeout(connect, 5000);
        }
      };
    };

    connect();

    return () => {
      cancelled = true;
      clearTimeout(reconnectTimer);
      socket?.close();
    };
  }, []);

  const resetSelection = useCallback(() => {
    setStep(STEP.TOKEN);
    setToken("");
    setSelectedCandidate(null);
    setErrorMessage("");
    setLoading(false);
  }, []);

  // auto-reset nakon neaktivnosti - ne racuna se na pocetnom ekranu (nema sto
  // resetirati) niti na success ekranu (taj se vec sam gasi brze)
  useEffect(() => {
    if (step === STEP.TOKEN || step === STEP.SUCCESS) {
      return undefined;
    }
    idleTimerRef.current = setTimeout(resetSelection, IDLE_RESET_MS);
    return () => clearTimeout(idleTimerRef.current);
  }, [step, resetSelection]);

  const showError = (code) => {
    setErrorMessage(translateError(code));
    setStep(STEP.ERROR);
    setLoading(false);
  };

  const handleTokenSubmit = async (rawToken) => {
    setLoading(true);
    try {
      await validateToken(rawToken);
      let currentCandidates = candidates;
      if (currentCandidates.length === 0) {
        // Kandidati mozda jos nisu ucitani (npr. izbor je otvoren TEK NAKON
        // sto je ovaj terminal vec bio pokrenut) - prije nego birac dobije
        // gresku, pokusaj jos jednom dohvatiti trenutni izbor.
        const election = await fetchCurrentElection();
        if (election) {
          setElectionName(election.election_name);
          setCandidates(election.candidates);
          currentCandidates = election.candidates;
        } else {
          currentCandidates = [];
        }
      }
      if (currentCandidates.length === 0) {
        showError("ELECTION_NOT_OPEN");
        return;
      }
      setToken(rawToken);
      setStep(STEP.CANDIDATES);
    } catch (err) {
      showError(err instanceof ApiError ? err.errorCode : "NETWORK_ERROR");
    } finally {
      setLoading(false);
    }
  };

  const handleVoteConfirm = async () => {
    setLoading(true);
    try {
      await castVote(token, selectedCandidate.id);
      setStep(STEP.SUCCESS);
      setTimeout(resetSelection, SUCCESS_DISPLAY_MS);
    } catch (err) {
      showError(err instanceof ApiError ? err.errorCode : "NETWORK_ERROR");
    } finally {
      setLoading(false);
    }
  };

  const tintClass =
    step === STEP.SUCCESS ? " kiosk-tint--success" : step === STEP.ERROR ? " kiosk-tint--error" : "";

  return (
    <div className="kiosk-background">
      {/* Poseban sloj preko cijelog ekrana - boja se mijenja s CSS
          tranzicijom (glatki fade), ne naglo, i ne smeta klikovima
          ispod sebe (pointer-events: none). */}
      <div className={`kiosk-tint${tintClass}`} aria-hidden="true" />
      <div className="kiosk-shell">
        <KioskHeader electionName={electionName} compact={step !== STEP.TOKEN} />

        <div className="kiosk-card">
          {step === STEP.TOKEN && <TokenEntryScreen onSubmit={handleTokenSubmit} loading={loading} />}

          {step === STEP.CANDIDATES && (
            <CandidateSelectScreen
              electionName={null}
              candidates={candidates}
              selected={selectedCandidate}
              onSelect={setSelectedCandidate}
              onContinue={() => setStep(STEP.CONFIRM)}
            />
          )}

          {step === STEP.CONFIRM && (
            <ConfirmScreen
              candidate={selectedCandidate}
              loading={loading}
              onConfirm={handleVoteConfirm}
              onBack={() => setStep(STEP.CANDIDATES)}
            />
          )}

          {step === STEP.SUCCESS && <SuccessScreen />}

          {step === STEP.ERROR && <ErrorScreen message={errorMessage} onRetry={resetSelection} />}
        </div>
      </div>
    </div>
  );
}
