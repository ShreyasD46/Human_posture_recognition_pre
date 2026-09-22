import { Link } from "react-router-dom";
import "./Landing.css";

export default function Landing() {
  return (
    <div className="landing-wrapper">
      <div className="mesh-bg"></div>
      
      <section className="hero">
        <div className="hero-content">
          <div className="hero-eyebrow">
            <span className="sparkle">✨</span> Human posture recognition, right in your browser
          </div>
          <h1>Practice yoga with a coach that watches your alignment, not your camera roll.</h1>
          <p className="lede">
            Sthira reads your joints through your webcam, checks each asana against a
            reference alignment in real time, and speaks a gentle correction the moment your
            form drifts. No lag, no videos saved.
          </p>
          <div className="hero-cta">
            <Link to="/signup"><button className="btn btn-primary">Start practicing</button></Link>
            <Link to="/login" className="muted-link">
              I already have an account →
            </Link>
          </div>
        </div>
        <div className="hero-figure-wrapper">
          <div className="hero-figure">
            <img src="/hero_illustration.jpg" alt="Person meditating" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
          </div>
          
          <div className="floating-stat float-1">
            <div className="num">97.8%</div>
            <div className="cap">Accuracy</div>
          </div>
          <div className="floating-stat float-2">
            <div className="num">33</div>
            <div className="cap">Keypoints</div>
          </div>
          <div className="floating-stat float-3">
            <div className="num">&lt;300ms</div>
            <div className="cap">Latency</div>
          </div>
        </div>
      </section>

      <section className="feature-row">
        <h2 className="section-title">Everything a solo practice needs.</h2>
        <div className="feature-grid">
          <div className="feature-card">
            <div className="mark">🗣️</div>
            <h3>Real-time voice correction</h3>
            <p>A deterministic rule engine compares your joint angles to reference alignment every frame and speaks a short cue the moment something drifts out of tolerance.</p>
          </div>
          <div className="feature-card">
            <div className="mark">📊</div>
            <h3>Instant session reports</h3>
            <p>Once you finish, an AI agent turns your aggregated data into a plain-language summary and specific tips for next time. We never process raw video.</p>
          </div>
          <div className="feature-card">
            <div className="mark">🧘</div>
            <h3>Five poses, done precisely</h3>
            <p>Tadasana, Vrikshasana, Trikonasana, Warrior II and Utkatasana — each with dedicated reference angles for highly accurate, specific feedback.</p>
          </div>
        </div>
      </section>
    </div>
  );
}


