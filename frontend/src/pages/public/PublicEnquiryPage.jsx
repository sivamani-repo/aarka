import React, { useState } from 'react';
import { SunMedium, CheckCircle, ArrowRight, ShieldCheck, Zap, Calculator, Landmark } from 'lucide-react';
import { publicAPI } from '../../services/api';

export const PublicEnquiryPage = () => {
  const [formData, setFormData] = useState({
    customer_name: '',
    phone: '',
    email: '',
    address: '',
    city: '',
    customer_category: 'Residential',
    preferred_contact_method: 'Phone',
    lead_source: 'Website',
    required_capacity: 3.0,
    solar_requirement: 'On-Grid',
    monthly_electricity_bill: 0,
    subsidy_requirement: false,
    additional_requirements: '',
    consent: false,
  });

  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const res = await publicAPI.submitEnquiry({
        ...formData,
        required_capacity: parseFloat(formData.required_capacity),
        monthly_electricity_bill: parseFloat(formData.monthly_electricity_bill),
      });
      setResult(res.data);
      setSubmitted(true);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to submit enquiry. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ minHeight: '100vh', backgroundColor: '#f5f6f3' }}>
      {/* Top Navigation */}
      <header
        style={{
          backgroundColor: '#0c2318',
          padding: '16px 32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          color: '#ffffff',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div
            style={{
              width: '36px',
              height: '36px',
              borderRadius: '10px',
              backgroundColor: '#2e8b60',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <SunMedium size={22} color="#fef08a" />
          </div>
          <div>
            <div style={{ fontSize: '18px', fontWeight: '800', fontFamily: 'var(--font-display)', letterSpacing: '0.04em' }}>
              AARKA
            </div>
            <div style={{ fontSize: '11px', color: '#94bca7' }}>Solar Operations, Simplified.</div>
          </div>
        </div>

        <a href="/login" className="btn btn-secondary btn-sm" style={{ backgroundColor: 'transparent', color: '#ffffff', borderColor: '#23533a' }}>
          Internal Staff Login →
        </a>
      </header>

      {/* Hero Banner */}
      <div
        style={{
          backgroundColor: '#143e2b',
          color: '#ffffff',
          padding: '48px 24px 64px',
          textAlign: 'center',
          background: 'linear-gradient(180deg, #0c2318 0%, #174530 100%)',
        }}
      >
        <div style={{ maxWidth: '750px', margin: '0 auto' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '6px',
              backgroundColor: 'rgba(255, 255, 255, 0.1)',
              padding: '6px 14px',
              borderRadius: '20px',
              fontSize: '12px',
              fontWeight: '600',
              marginBottom: '16px',
              color: '#d4ebd9',
            }}
          >
            <Landmark size={14} color="#f59e0b" /> Scheme eligibility is subject to official verification
          </div>
          <h1 style={{ fontSize: '36px', fontWeight: '800', color: '#ffffff', marginBottom: '12px', fontFamily: 'var(--font-display)' }}>
            Explore a rooftop solar installation for your property
          </h1>
          <p style={{ fontSize: '16px', color: '#b9d6c6', lineHeight: 1.6 }}>
            Share your requirements for a consultation. System suitability, pricing, warranty coverage, and any government scheme eligibility are confirmed separately.
          </p>
        </div>
      </div>

      {/* Main Form Container */}
      <div style={{ maxWidth: '800px', margin: '-36px auto 60px', padding: '0 20px' }}>
        <div className="aarka-card" style={{ padding: '36px', boxShadow: 'var(--shadow-lg)' }}>
          {submitted ? (
            <div style={{ textAlign: 'center', padding: '32px 16px' }}>
              <div
                style={{
                  width: '64px',
                  height: '64px',
                  borderRadius: '50%',
                  backgroundColor: 'var(--color-primary-50)',
                  color: 'var(--color-primary-600)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  margin: '0 auto 16px',
                }}
              >
                <CheckCircle size={36} />
              </div>
              <h2 style={{ fontSize: '24px', fontWeight: '800', marginBottom: '8px' }}>
                Enquiry Successfully Received!
              </h2>
              <p style={{ fontSize: '15px', color: 'var(--text-muted)', marginBottom: '24px', maxWidth: '520px', margin: '0 auto 24px' }}>
                {result?.message}
              </p>

              <div
                style={{
                  backgroundColor: 'var(--bg-subtle)',
                  padding: '20px',
                  borderRadius: 'var(--radius-md)',
                  display: 'inline-block',
                  textAlign: 'left',
                  marginBottom: '28px',
                  minWidth: '320px',
                }}
              >
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>
                  Your Lead Reference Number
                </div>
                <div style={{ fontSize: '26px', fontWeight: '800', color: 'var(--color-primary-700)', fontFamily: 'var(--font-display)' }}>
                  {result?.lead_reference}
                </div>
                <div style={{ fontSize: '13px', color: 'var(--text-main)', marginTop: '6px' }}>
                  Capacity: <strong>{formData.required_capacity} kW {formData.solar_requirement}</strong>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'center', gap: '16px' }}>
                <button
                  className="btn btn-secondary"
                  onClick={() => {
                    setSubmitted(false);
                    setResult(null);
                  }}
                >
                  Submit Another Enquiry
                </button>
                <a href="/login" className="btn btn-primary">
                  View in Staff Dashboard <ArrowRight size={16} />
                </a>
              </div>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontSize: '20px', fontWeight: '700', marginBottom: '6px' }}>
                  Request Solar Consultation & Rooftop Survey
                </h3>
                <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                  Fill in your details below to calculate capacity, estimated generation, and get a technical site inspection.
                </p>
              </div>

              {error && (
                <div style={{ padding: '12px', backgroundColor: 'var(--color-rose-50)', color: 'var(--color-rose-600)', borderRadius: 'var(--radius-md)', marginBottom: '16px', fontSize: '13px' }}>
                  {error}
                </div>
              )}

              {/* Grid 2 Column */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Full Name *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    value={formData.customer_name}
                    onChange={(e) => setFormData({ ...formData, customer_name: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Phone Number *</label>
                  <input
                    type="tel"
                    required
                    className="form-control"
                    value={formData.phone}
                    onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">Email Address</label>
                  <input
                    type="email"
                    className="form-control"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">City *</label>
                  <input
                    type="text"
                    required
                    className="form-control"
                    value={formData.city}
                    onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  />
                </div>
              </div>

              <div className="form-group">
                <label className="form-label">Installation Address *</label>
                <input
                  type="text"
                  required
                  className="form-control"
                  placeholder="Plot / House number, Street, Landmark"
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                />
              </div>

              {/* Technical Requirements */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '16px', marginTop: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Required Capacity</label>
                  <select
                    className="form-select"
                    value={formData.required_capacity}
                    onChange={(e) => setFormData({ ...formData, required_capacity: parseFloat(e.target.value) })}
                  >
                    <option value={1.0}>1 kW (4-5 units/day)</option>
                    <option value={2.0}>2 kW (8-10 units/day)</option>
                    <option value={3.0}>3 kW (12-15 units/day) [Most Popular]</option>
                    <option value={4.0}>4 kW (16-20 units/day)</option>
                    <option value={5.0}>5 kW (20-25 units/day)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">System Type</label>
                  <select
                    className="form-select"
                    value={formData.solar_requirement}
                    onChange={(e) => setFormData({ ...formData, solar_requirement: e.target.value })}
                  >
                    <option value="On-Grid">On-Grid (Net Metering)</option>
                    <option value="Off-Grid">Off-Grid (With Battery)</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Monthly Electricity Bill (₹)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={formData.monthly_electricity_bill}
                    onChange={(e) => setFormData({ ...formData, monthly_electricity_bill: parseFloat(e.target.value) || 0 })}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div className="form-group">
                  <label className="form-label">Customer Category</label>
                  <select
                    className="form-select"
                    value={formData.customer_category}
                    onChange={(e) => setFormData({ ...formData, customer_category: e.target.value })}
                  >
                    <option value="Residential">Residential Homeowner</option>
                    <option value="Commercial">Commercial / SME Enterprise</option>
                  </select>
                </div>

                <div className="form-group">
                  <label className="form-label">Preferred Contact</label>
                  <select
                    className="form-select"
                    value={formData.preferred_contact_method}
                    onChange={(e) => setFormData({ ...formData, preferred_contact_method: e.target.value })}
                  >
                    <option value="Phone">Phone Call</option>
                    <option value="WhatsApp">WhatsApp</option>
                    <option value="Email">Email</option>
                  </select>
                </div>
              </div>

              {/* Subsidy Assistance checkbox */}
              <div style={{ backgroundColor: 'var(--color-primary-50)', padding: '14px 16px', borderRadius: 'var(--radius-md)', marginBottom: '16px', border: '1px solid var(--color-primary-200)' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer', fontSize: '14px', fontWeight: '600', color: 'var(--color-primary-800)' }}>
                  <input
                    type="checkbox"
                    checked={formData.subsidy_requirement}
                    onChange={(e) => setFormData({ ...formData, subsidy_requirement: e.target.checked })}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary-700)' }}
                  />
                  <span>I would like information about any subsidy for which my project may be eligible.</span>
                </label>
              </div>

              <div className="form-group">
                <label className="form-label">Additional Observations or Special Requirements</label>
                <textarea
                  rows={2}
                  className="form-textarea"
                  value={formData.additional_requirements}
                  onChange={(e) => setFormData({ ...formData, additional_requirements: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label style={{ display: 'flex', alignItems: 'flex-start', gap: '10px', fontSize: '13px' }}>
                  <input
                    type="checkbox"
                    required
                    checked={formData.consent}
                    onChange={(e) => setFormData({ ...formData, consent: e.target.checked })}
                  />
                  <span>I consent to AARKA using these details to respond to my enquiry.</span>
                </label>
              </div>

              <button
                type="submit"
                className="btn btn-primary btn-lg"
                style={{ width: '100%', marginTop: '12px' }}
                disabled={loading}
              >
                {loading ? 'Submitting to AARKA...' : 'Submit Solar Installation Enquiry'}
                <ArrowRight size={18} />
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
};



export default PublicEnquiryPage;
