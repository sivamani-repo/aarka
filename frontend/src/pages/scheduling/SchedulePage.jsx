import React, { useState, useEffect } from 'react';
import { Calendar, Clock, MapPin, Wrench, Zap, ClipboardCheck } from 'lucide-react';
import { surveysAPI, installationsAPI, techniciansAPI } from '../../services/api';
import { StatusBadge } from '../../components/common/StatusBadge';

export const SchedulePage = () => {
  const [surveys, setSurveys] = useState([]);
  const [installations, setInstallations] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filterView, setFilterView] = useState('ALL'); // ALL, SURVEYS, INSTALLATIONS

  useEffect(() => {
    const fetchSchedule = async () => {
      setLoading(true);
      try {
        const [survRes, instRes, techRes] = await Promise.all([
          surveysAPI.getSurveys(),
          installationsAPI.getInstallations(),
          techniciansAPI.getTechnicians(),
        ]);
        setSurveys(survRes.data);
        setInstallations(instRes.data);
        setTechnicians(techRes.data);
      } catch (err) {
        console.error('Failed to load schedule:', err);
      } finally {
        setLoading(false);
      }
    };
    fetchSchedule();
  }, []);

  return (
    <div>
      {/* Top Filter Buttons */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: '800' }}>Field Operations Master Schedule</h2>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Centralized calendar dispatch of 15 technicians for roof inspections and project installations
          </p>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            className={`btn btn-sm ${filterView === 'ALL' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterView('ALL')}
          >
            All Deployments
          </button>
          <button
            className={`btn btn-sm ${filterView === 'SURVEYS' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterView('SURVEYS')}
          >
            <ClipboardCheck size={14} /> Site Surveys
          </button>
          <button
            className={`btn btn-sm ${filterView === 'INSTALLATIONS' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setFilterView('INSTALLATIONS')}
          >
            <Zap size={14} /> Installations
          </button>
        </div>
      </div>

      {/* Grid of Scheduled Events */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(360px, 1fr))', gap: '16px' }}>
        {(filterView === 'ALL' || filterView === 'INSTALLATIONS') &&
          installations.map((inst) => (
            <div key={`inst-${inst.id}`} className="aarka-card" style={{ padding: '18px', borderLeft: '4px solid var(--color-primary-600)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <span className="badge badge-success">
                  <Zap size={12} /> Installation Job
                </span>
                <StatusBadge status={inst.status} />
              </div>

              <div style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-main)', marginBottom: '4px' }}>
                {inst.job_number} • {inst.capacity_kw} kW System
              </div>

              <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                <strong>Customer:</strong> {inst.customer_name}
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-light)', marginBottom: '12px' }}>
                <MapPin size={12} style={{ display: 'inline' }} /> {inst.customer_address}
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-primary-800)', fontWeight: '600' }}>
                  <Wrench size={14} />
                  <span>{inst.technician_name || 'Unassigned'}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)' }}>
                  <Calendar size={13} />
                  <span>{inst.scheduled_date || 'TBD'}</span>
                </div>
              </div>
            </div>
          ))}

        {(filterView === 'ALL' || filterView === 'SURVEYS') &&
          surveys.map((surv) => (
            <div key={`surv-${surv.id}`} className="aarka-card" style={{ padding: '18px', borderLeft: '4px solid var(--color-amber-500)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '10px' }}>
                <span className="badge badge-warning">
                  <ClipboardCheck size={12} /> Site Survey
                </span>
                <StatusBadge status={surv.status} />
              </div>

              <div style={{ fontSize: '16px', fontWeight: '700', color: 'var(--text-main)', marginBottom: '4px' }}>
                {surv.survey_reference} • {surv.required_capacity_kw} kW Proposed
              </div>

              <div style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '8px' }}>
                <strong>Customer:</strong> {surv.customer_name}
              </div>

              <div style={{ fontSize: '12px', color: 'var(--text-light)', marginBottom: '12px' }}>
                <MapPin size={12} style={{ display: 'inline' }} /> {surv.customer_address}
              </div>

              <div style={{ borderTop: '1px solid var(--border-color)', paddingTop: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: 'var(--color-primary-800)', fontWeight: '600' }}>
                  <Wrench size={14} />
                  <span>{surv.technician_name || 'Unassigned'}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--text-muted)' }}>
                  <Calendar size={13} />
                  <span>{surv.scheduled_date || 'TBD'}</span>
                </div>
              </div>
            </div>
          ))}
      </div>
    </div>
  );
};



export default SchedulePage;
