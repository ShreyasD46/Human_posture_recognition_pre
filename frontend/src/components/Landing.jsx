import { Link } from "react-router-dom";
import "./Landing.css";

export default function Landing() {
  return (
    <div className="landing-wrapper">
      <div className="mesh-bg"></div>

      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-eyebrow">
            <span className="sparkle">💪</span> AI-Powered Fitness Coaching — Gym &amp; Yoga
          </div>
          <h1>
            Your body is the data.<br />
            Real-time form coaching for every rep and every hold.
          </h1>
          <p className="lede">
            Sthira uses your webcam to track 33 body keypoints, checks your form against
            reference angles every frame, and guides you with live skeleton overlays and
            audio cues — for gym exercises <em>and</em> yoga poses. No video stored. No lag.
          </p>
          <div className="hero-cta">
            <Link to="/signup"><button className="btn btn-primary">Start training free</button></Link>
            <Link to="/login" className="muted-link">
              I already have an account →
            </Link>
          </div>
        </div>
        <div className="hero-figure-wrapper">
          <div className="hero-figure">
            <img src="/hero_illustration.jpg" alt="AI fitness coaching" style={{ width: "100%", height: "100%", objectFit: "cover" }} />
          </div>

          <div className="floating-stat float-1">
            <div className="num">20+ FPS</div>
            <div className="cap">On Pi 4B</div>
          </div>
          <div className="floating-stat float-2">
            <div className="num">33</div>
            <div className="cap">Keypoints</div>
          </div>
          <div className="floating-stat float-3">
            <div className="num">&lt;150ms</div>
            <div className="cap">Latency</div>
          </div>
        </div>
      </section>

      {/* ── Category cards ── */}
      <section className="feature-row">
        <h2 className="section-title">Two disciplines. One AI coach.</h2>
        <div className="feature-grid">
          <div className="feature-card" style={{ borderTop: "3px solid #f97316" }}>
            <div className="mark">🏋️</div>
            <h3>Gym Workouts</h3>
            <p>
              Push-ups, bicep curls, bench press, lateral raises and more — with per-rep
              counting, tempo tracking, range-of-motion scoring, and a ghost skeleton
              showing perfect form alongside yours.
            </p>
          </div>
          <div className="feature-card" style={{ borderTop: "3px solid #a78bfa" }}>
            <div className="mark">🧘</div>
            <h3>Yoga Poses</h3>
            <p>
              Tadasana, Vrikshasana, Trikonasana, Warrior II, Utkatasana — with hold
              timers, alignment score, breathing cadence guides, and real-time joint-angle
              feedback for precise asana practice.
            </p>
          </div>
        </div>
      </section>

      {/* ── Feature list ── */}
      <section className="feature-row">
        <h2 className="section-title">Everything a serious training session needs.</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="mark">👻</div>
            <h3>Ghost Skeleton Overlay</h3>
            <p>
              A translucent reference skeleton retargeted to your own body proportions
              shows ideal form for every exercise phase. Know exactly where to move, not
              just told what to do.
            </p>
          </div>
          <div className="feature-card">
            <div className="mark">🎨</div>
            <h3>Color-Coded Joints</h3>
            <p>
              Every bone and joint is green (correct), amber (minor deviation), or red
              (major error) in real time — instantly readable from 2–3 metres away on a
              kiosk display.
            </p>
          </div>
          <div className="feature-card">
            <div className="mark">🗣️</div>
            <h3>Rate-Limited Voice Cues</h3>
            <p>
              Audio coaching fires when needed, never nags. Beginner, intermediate, and
              advanced cooldown modes keep cues useful without becoming white noise.
            </p>
          </div>
          <div className="feature-card">
            <div className="mark">📊</div>
            <h3>AI Session Summary</h3>
            <p>
              Post-session analytics cover form trends, left/right asymmetry, tempo
              consistency, fatigue drop-off, personal bests, and a human-readable
              coach narrative — offline-capable.
            </p>
          </div>
          <div className="feature-card">
            <div className="mark">👥</div>
            <h3>Multi-User Kiosk</h3>
            <p>
              Gym-grade multi-user login with PIN or QR badge scan, Argon2-hashed
              credentials, role-based access (Member / Trainer / Admin), and
              per-user isolated progress history.
            </p>
          </div>
          <div className="feature-card">
            <div className="mark">🔒</div>
            <h3>Privacy-First, Edge-Native</h3>
            <p>
              Raw video never leaves your device. Only 33 coordinate vectors per frame
              are sent to the backend. No cloud dependency. Runs fully offline on a
              Raspberry Pi 4B.
            </p>
          </div>
        </div>
      </section>
    </div>
  );
}
