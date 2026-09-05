import grbUrl from "../assets/grb.png";

// FAZA 9 (dopuna) #19 - isti suptilni vodeni žig (grb + "Republika Hrvatska")
// kao na glasačkom terminalu (frontend-terminal/src/components/KioskHeader.jsx),
// da admin konzola djeluje kao dio iste službene aplikacije, ne kao odvojen
// alat.
//
// Dvije varijante:
// - fiksna (zadano) - kao na terminalu, u gornjem lijevom kutu EKRANA. Koristi
//   se na ekranu za prijavu (centrirana kartica, nema vlastitog zaglavlja).
// - "inline" (prop inline) - dio je normalnog toka unutar admin-headera na
//   Dashboardu (koji vec ima svoju naslovnu traku preko cijele sirine) - da
//   se ne preklapa s naslovom "E-Glasanje - Admin konzola" u istom kutu.
export default function AdminWatermark({ inline = false }) {
  return (
    <div className={`admin-watermark${inline ? " admin-watermark--inline" : ""}`} aria-hidden="true">
      <img src={grbUrl} alt="" className="admin-watermark-emblem" />
      <span className="admin-watermark-text">
        <span className="admin-watermark-line">Republika</span>
        <span className="admin-watermark-line">Hrvatska</span>
      </span>
    </div>
  );
}
