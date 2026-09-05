import grbUrl from "../assets/grb.png";

// Dva stanja naziva izbora (dogovoreno s korisnikom):
// - "veliki" naslov iznad kartice dok birac tek unosi kljuc (STEP.TOKEN) - tu
//   ima dovoljno praznog prostora, a naziv izbora treba biti upadljiv.
// - nakon unosa koda (svi ostali koraci), naziv se "skuplja" i seli u grb u
//   gornjem lijevom kutu ekrana, odvojen tankom crtom - isti obrazac kao u
//   admin konzoli - jer kartica onda ima svoj sadrzaj (kandidati, potvrda...)
//   i veliki naslov bi samo oduzimao prostor/ponavljao se.
export default function KioskHeader({ electionName, compact = false }) {
  if (compact && electionName) {
    return (
      <div className="kiosk-watermark kiosk-watermark--with-title">
        <img src={grbUrl} alt="" className="kiosk-watermark-emblem" />
        <span className="kiosk-watermark-text">
          <span className="kiosk-watermark-line">Republika</span>
          <span className="kiosk-watermark-line">Hrvatska</span>
        </span>
        <span className="kiosk-watermark-election">{electionName}</span>
      </div>
    );
  }

  return (
    <>
      {/* Grb + "Republika Hrvatska" - suptilan vodeni žig fiksiran u gornjem
          lijevom kutu ekrana, uvijek prisutan. */}
      <div className="kiosk-watermark" aria-hidden="true">
        <img src={grbUrl} alt="" className="kiosk-watermark-emblem" />
        <span className="kiosk-watermark-text">
          <span className="kiosk-watermark-line">Republika</span>
          <span className="kiosk-watermark-line">Hrvatska</span>
        </span>
      </div>

      {electionName && (
        <div className="kiosk-page-header">
          <p className="kiosk-header-title-big">{electionName}</p>
        </div>
      )}
    </>
  );
}
