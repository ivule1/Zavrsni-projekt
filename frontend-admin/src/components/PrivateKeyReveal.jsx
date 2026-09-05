import { useRef, useState } from "react";

// Zajednicki prikaz privatnog kljuca koji se pokazuje TOCNO JEDNOM - ili
// odmah pri otvaranju izbora (rucno "Otvori izbor"), ili odmah pri kreiranju
// izbora s zakazanim otvaranjem (FAZA 9 dopuna - kljuc se generira i
// prikazuje ODMAH jer je admin tada prisutan, a ne tek u trenutku
// automatskog otvaranja kad nitko ne mora gledati ekran). Izdvojeno iz
// CandidateManagera da se ista logika (kopiranje, upozorenje) ne duplicira.
export default function PrivateKeyReveal({ privateKeyPem, heading, onAcknowledge }) {
  const [copied, setCopied] = useState(false);
  const [copyError, setCopyError] = useState("");
  const keyTextareaRef = useRef(null);

  const handleCopyKey = async () => {
    // navigator.clipboard.writeText kopira TOCAN JS string (uklj. stvarne
    // znakove novog retka \n iz PEM-a), bez obzira na to kako je tekst
    // vizualno prelomljen/renderiran u textarei.
    try {
      await navigator.clipboard.writeText(privateKeyPem);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch {
      // Clipboard API moze biti odbijen (npr. bez dozvole preglednika) -
      // tada barem odmah markiraj cijeli tekst da Ctrl+C radi bez trazenja.
      keyTextareaRef.current?.select();
      setCopyError("Automatsko kopiranje nije uspjelo - tekst je markiran, koristi Ctrl+C.");
    }
  };

  return (
    <div className="tally-warning">
      <p className="mb-2">
        <strong>{heading}</strong> Ovo je privatni ključ za dešifriranje glasova - prikazuje se{" "}
        <strong>samo ovaj jedan put</strong>. Spremi ga izvan sustava (poglavlje 34.1) - bez njega glasovi
        se NE MOGU prebrojati nakon zatvaranja izbora.
      </p>
      <textarea
        ref={keyTextareaRef}
        className="form-control mb-2"
        rows={8}
        readOnly
        style={{ fontFamily: "monospace", fontSize: "0.75rem" }}
        value={privateKeyPem}
        onFocus={(e) => e.target.select()}
      />
      {copyError && <div className="alert alert-danger py-2">{copyError}</div>}
      <div className="d-flex gap-2 flex-wrap align-items-center">
        <button type="button" className="btn admin-btn text-white btn-sm" onClick={handleCopyKey}>
          {copied ? "Kopirano ✓" : "Kopiraj ključ"}
        </button>
        <button type="button" className="btn btn-outline-secondary btn-sm" onClick={onAcknowledge}>
          U redu, spremio/la sam ključ
        </button>
      </div>
    </div>
  );
}
