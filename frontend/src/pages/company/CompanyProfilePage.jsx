import React from 'react';
import {
  Award,
  BadgeCheck,
  BriefcaseBusiness,
  Building2,
  ClipboardCheck,
  FileBadge,
  Factory,
  Handshake,
  HeartHandshake,
  Layers3,
  ShieldCheck,
  SunMedium,
} from 'lucide-react';

const serviceAreas = [
  {
    icon: ClipboardCheck,
    title: 'Project planning',
    description:
      'Capture customer requirements, coordinate site surveys, and organize solar project proposals.',
  },
  {
    icon: Layers3,
    title: 'Sales and project coordination',
    description:
      'Manage packages, quotations, orders, payments, and project information in one workflow.',
  },
  {
    icon: Factory,
    title: 'Inventory and field operations',
    description:
      'Track equipment and serial numbers while coordinating dispatches, schedules, and installations.',
  },
  {
    icon: HeartHandshake,
    title: 'Customer support',
    description:
      'Keep warranty records and service requests connected to the customer and installed equipment.',
  },
  {
    icon: Handshake,
    title: 'Supplier and subsidy workflows',
    description:
      'Organize supplier information and supporting documentation for government subsidy processes.',
  },
  {
    icon: BriefcaseBusiness,
    title: 'Business oversight',
    description:
      'Review operational reports, financial information, and team activity from a shared workspace.',
  },
];

const credentials = [
  {
    icon: Award,
    title: 'Industry experience',
    description: 'Years in business and project track record have not been provided.',
  },
  {
    icon: BadgeCheck,
    title: 'Rankings and awards',
    description: 'No independently verifiable rankings or awards have been added.',
  },
  {
    icon: ShieldCheck,
    title: 'Certifications and licenses',
    description: 'No certificate or license records have been provided for display.',
  },
  {
    icon: FileBadge,
    title: 'Legal registrations and rights',
    description:
      'Company registration, statutory identifiers, and other legal records require verified details.',
  },
];

export default function CompanyProfilePage() {
  return (
    <div className="company-profile">
      <section className="company-profile-hero">
        <div className="company-profile-hero-copy">
          <span className="company-profile-eyebrow">
            <Building2 size={14} />
            Company profile
          </span>
          <h1>AARKA Solar</h1>
          <p className="company-profile-tagline">Solar Operations, Simplified.</p>
          <p className="company-profile-intro">
            AARKA brings solar project workflows together, from customer enquiry
            and planning through installation coordination and after-sales
            support.
          </p>
        </div>
        <div className="company-profile-hero-mark" aria-hidden="true">
          <SunMedium size={64} strokeWidth={1.2} />
          <span>Solar project operations</span>
        </div>
      </section>

      <section className="company-profile-section" aria-labelledby="services-title">
        <div className="company-profile-section-heading">
          <div>
            <span className="company-profile-eyebrow">What we do</span>
            <h2 id="services-title">Platform-supported service areas</h2>
          </div>
          <p>
            These are the capabilities represented in the AARKA platform; they
            are not a substitute for confirming the company&apos;s contracted
            services.
          </p>
        </div>
        <div className="company-profile-service-grid">
          {serviceAreas.map(({ icon: Icon, title, description }) => (
            <article className="company-profile-card" key={title}>
              <span className="company-profile-card-icon">
                <Icon size={20} />
              </span>
              <h3>{title}</h3>
              <p>{description}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="company-profile-section" aria-labelledby="credentials-title">
        <div className="company-profile-section-heading">
          <div>
            <span className="company-profile-eyebrow">Verified company details</span>
            <h2 id="credentials-title">Experience, recognition and credentials</h2>
          </div>
          <p>
            Official claims should be published only after the supporting
            information has been verified.
          </p>
        </div>
        <div className="company-profile-credential-grid">
          {credentials.map(({ icon: Icon, title, description }) => (
            <article className="company-profile-credential" key={title}>
              <Icon size={19} />
              <div>
                <h3>{title}</h3>
                <p>{description}</p>
                <span className="company-profile-unverified">
                  <ShieldCheck size={13} />
                  Details not provided
                </span>
              </div>
            </article>
          ))}
        </div>
      </section>

      <aside className="company-profile-note">
        <BadgeCheck size={19} />
        <p>
          To show company experience, rankings, registrations, licenses, or
          certifications here, add the verified details and supporting
          references to the company profile.
        </p>
      </aside>
    </div>
  );
}
