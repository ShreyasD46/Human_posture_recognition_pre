import { Link } from "react-router-dom";
import "./Landing.css";

const FEATURES = [
  { icon: "👻", title: "Ghost Skeleton Overlay", desc: "A translucent reference skeleton retargeted to your body proportions shows ideal form for every exercise phase — not just text cues." },
  { icon: "🎨", title: "Color-Coded Joints", desc: "Every joint turns green (correct), amber (slight drift), or red (needs correction) in real time, readable from 3 metres." },
  { icon: "🧮", title: "Rep State Machine", desc: "Hysteresis-based FSM counts reps with zero false positives, tracks tempo, detects breaks, and records every rep's form score." },
  { icon: "🗣️", title: "Rate-Limited Audio Coach", desc: "Voice cues fire only when genuinely needed. Beginner, default, and advanced cooldown modes prevent coaching fatigue." },
  { icon: "📊", title: "AI Session Summary", desc: "Post-session analytics cover form trends, left/right asymmetry, tempo consistency, fatigue drop-off and personal bests — fully offline." },
  { icon: "🔒", title: "Privacy-First Edge", desc: "Raw video never leaves your device. Only 33 coordinate vectors per frame reach the backend. No cloud required." },
];

export default function Landing() {
  return (
    <div className="landing-wrapper">
      <div className="mesh-bg" />

      {/* ── Hero ── */}
      <section className="hero">
        <div className="hero-content">
          <div className="hero-eyebrow">
            <span className="sparkle">⚡</span>
            AI Fitness Coaching — Gym &amp; Yoga
          </div>

          <h1>
            Train with a coach<br />
            that sees every<br />
            <em>single rep.</em>
          </h1>

          <p className="lede">
            Sthira uses your webcam to track 33 body keypoints, overlays a
            ghost reference skeleton on your live video, and coaches you
            with real-time color-coded feedback — for gym workouts
            <strong style={{ color: "var(--gym)" }}> and</strong> yoga poses.
            Runs fully offline on a Raspberry Pi 4B.
          </p>

          <div className="hero-cta">
            <Link to="/signup">
              <button className="btn btn-primary" style={{ fontSize: 16, padding: "14px 36px" }}>
                Start training free
              </button>
            </Link>
            <Link to="/login" className="muted-link">
              Already a member? Sign in →
            </Link>
          </div>
        </div>

        <div className="hero-figure-wrapper">
          <div className="hero-figure">
            <img
              src="/hero_illustration.jpg"
              alt="AI fitness coaching skeleton overlay"
              style={{ width: "100%", height: "100%", objectFit: "cover", position: "relative", zIndex: 2 }}
            />
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

      {/* ── Category duo ── */}
      <div className="category-duo">
        <div className="category-card gym">
          <span className="category-icon">🏋️</span>
          <h3 style={{ color: "var(--gym)" }}>Gym Training</h3>
          <p>
            Push-ups, bicep curls, bench press, lateral raises and more — with
            per-rep counting, tempo tracking, range-of-motion scoring, and a
            ghost reference skeleton showing perfect form alongside yours.
          </p>
        </div>
        <div className="category-card yoga">
          <span className="category-icon">🧘</span>
          <h3 style={{ color: "var(--yoga)" }}>Yoga Practice</h3>
          <p>
            Tadasana, Vrikshasana, Trikonasana, Warrior II, Utkatasana — with
            hold timers, alignment scoring, breathing cadence guides, and
            real-time joint-angle feedback for precise asana practice.
          </p>
        </div>
      </div>

      {/* ── Features ── */}
      <section className="feature-row">
        <h2 className="section-title">Everything serious training needs.</h2>
        <p className="section-sub">
          Built for gyms, designed to run on a Raspberry Pi 4B, sold to real trainers.
        </p>
        <div className="feature-grid">
          {FEATURES.map((f) => (
            <div className="feature-card" key={f.title}>
              <div className="mark">{f.icon}</div>
              <h3>{f.title}</h3>
              <p>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
