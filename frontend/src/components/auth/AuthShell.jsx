import React, { useEffect, useState } from 'react';
import { useLocation } from 'react-router-dom';

const services = [
  {
    icon: '☀',
    title: 'Solar Solutions',
    description: 'Manage solar systems and energy solutions.',
  },
  {
    icon: '⚡',
    title: 'Installation Management',
    description: 'Track projects from enquiry through installation.',
  },
  {
    icon: '◈',
    title: 'Customer Management',
    description: 'Keep customer and service activity organized.',
  },
];

export default function AuthShell({ mode, children }) {
  const location = useLocation();
  const [isSwitching, setIsSwitching] = useState(
    Boolean(location.state?.authSwitch),
  );

  useEffect(() => {
    if (!isSwitching) return undefined;

    const timer = window.setTimeout(() => setIsSwitching(false), 600);
    return () => window.clearTimeout(timer);
  }, [isSwitching]);

  return (
    <main
      className={`aarka-auth-page ${mode === 'register' ? 'is-register' : ''} ${
        isSwitching ? 'is-switching' : ''
      }`}
    >
      <section className="auth-info-panel" aria-label="About AARKA">
        <div className="auth-brand">
          <div className="brand-icon" aria-hidden="true">☀</div>
          <div>
            <h2>AARKA</h2>
            <span>Solar Operations, Simplified.</span>
          </div>
        </div>

        <div className="auth-info-content">
          <span className="auth-eyebrow">SMART SOLAR MANAGEMENT</span>
          <h1>
            Powering a
            <span> Brighter Tomorrow.</span>
          </h1>
          <p>
            AARKA simplifies solar operations with intelligent management of
            customers, quotations, installations, and energy solutions.
          </p>

          <div className="auth-services">
            {services.map((service) => (
              <div className="service-item" key={service.title}>
                <span aria-hidden="true">{service.icon}</span>
                <div>
                  <h3>{service.title}</h3>
                  <p>{service.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        <figure className="auth-consultation">
          <img
            src="/aarka-solar-consultation.jpg"
            alt="Two solar professionals standing beside a solar array and discussing the installation"
          />
          <figcaption>
            <span>Clear guidance for your solar journey</span>
            <a
              href="https://commons.wikimedia.org/wiki/File:Technicians_working_on_a_solar_panel_installation_(9229).jpg"
              target="_blank"
              rel="noreferrer"
            >
              Photo: Stephen Yang / The Solutions Project · CC BY 2.0
            </a>
          </figcaption>
        </figure>

        <div className="auth-info-footer">
          © 2026 AARKA Solar System. All rights reserved.
        </div>
      </section>

      <section className="auth-form-panel" aria-label={mode === 'register' ? 'Create account' : 'Sign in'}>
        <div className="auth-form-container">{children}</div>
      </section>
    </main>
  );
}
