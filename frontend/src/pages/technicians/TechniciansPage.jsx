import React, { useState, useEffect } from 'react';
import { Plus, Wrench, Phone, Mail, Award, Calendar, CheckCircle } from 'lucide-react';
import { techniciansAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const TechniciansPage = () => {
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [selectedTech, setSelectedTech] = useState(null);
  const [techSchedule, setTechSchedule] = useState(null);

  const [newTech, setNewTech] = useState({
    name: '',
    phone: '',
    email: '',
    skills: 'Rooftop Mounts, Inverters, Electrical',
    experience_years: 3,
    availability: 'AVAILABLE',
    employment_status: 'FULL_TIME',
  });

  const fetchTechnicians = async () => {
    setLoading(true);
    try {
      const res = await techniciansAPI.getTechnicians();
      setTechnicians(res.data);
    } catch (err) {
      console.error('Failed to load technicians:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTechnicians();
  }, []);

  const handleAddTech = async (e) => {
    e.preventDefault();
    try {
      await techniciansAPI.createTechnician({
        ...newTech,
        experience_years: parseInt(newTech.experience_years),
      });
      setIsAddOpen(false);
      fetchTechnicians();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to add technician');
    }
  };

  const openSchedule = async (tech) => {
    setSelectedTech(tech);
    try {
      const res = await techniciansAPI.getTechnicianSchedule(tech.id);
      setTechSchedule(res.data);
      setIsScheduleOpen(true);
    } catch (err) {
      alert('Failed to load technician schedule');
    }
  };

  const columns = [
    {
      header: 'Technician Name',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '700', color: 'var(--text-main)' }}>{row.name}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.email || '—'}</div>
        </div>
      ),
    },
    {
      header: 'Contact Phone',
      accessor: 'phone',
      render: (row) => <span><Phone size={12} style={{ display: 'inline' }} /> {row.phone}</span>,
    },
    {
      header: 'Core Skills',
      accessor: 'skills',
      render: (row) => <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{row.skills}</span>,
    },
    {
      header: 'Experience',
      render: (row) => <span>{row.experience_years} years</span>,
    },
    {
      header: 'Active Deployments',
      render: (row) => (
        <span style={{ fontWeight: '700', color: row.active_assignments > 0 ? 'var(--color-primary-700)' : 'var(--text-muted)' }}>
          {row.active_assignments} active jobs
        </span>
      ),
    },
    {
      header: 'Availability',
      render: (row) => <StatusBadge status={row.availability} />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <button className="btn btn-secondary btn-sm" onClick={() => openSchedule(row)}>
          <Calendar size={13} /> View Jobs
        </button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <button className="btn btn-primary" onClick={() => setIsAddOpen(true)}>
          <Plus size={16} /> Add Field Technician
        </button>
      </div>

      <DataTable
        title="Field Technician Workforce (15 Personnel)"
        subtitle="Manage rooftop technicians, certifications, skill sets, and job deployments"
        columns={columns}
        data={technicians}
        searchKey="name"
        searchPlaceholder="Search technicians by name, skills..."
      />

      {/* Add Technician Modal */}
      <Modal isOpen={isAddOpen} onClose={() => setIsAddOpen(false)} title="Register New Field Technician">
        <form onSubmit={handleAddTech}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Full Name *</label>
              <input
                type="text"
                required
                className="form-control"
                value={newTech.name}
                onChange={(e) => setNewTech({ ...newTech, name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Phone Number *</label>
              <input
                type="tel"
                required
                className="form-control"
                value={newTech.phone}
                onChange={(e) => setNewTech({ ...newTech, phone: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-control"
                value={newTech.email}
                onChange={(e) => setNewTech({ ...newTech, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Experience (Years)</label>
              <input
                type="number"
                min={0}
                className="form-control"
                value={newTech.experience_years}
                onChange={(e) => setNewTech({ ...newTech, experience_years: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Technical Skills & Certifications</label>
            <input
              type="text"
              className="form-control"
              value={newTech.skills}
              onChange={(e) => setNewTech({ ...newTech, skills: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsAddOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Register Technician
            </button>
          </div>
        </form>
      </Modal>

      {/* Technician Schedule & Deployments Modal */}
      <Modal isOpen={isScheduleOpen} onClose={() => setIsScheduleOpen(false)} title={`Assigned Deployments: ${selectedTech?.name}`} maxWidth="700px">
        {techSchedule && (
          <div>
            <div style={{ backgroundColor: 'var(--color-primary-50)', padding: '14px', borderRadius: '8px', marginBottom: '16px', fontSize: '13px' }}>
              <div><strong>Skills:</strong> {selectedTech.skills}</div>
              <div><strong>Phone:</strong> {selectedTech.phone} • {selectedTech.experience_years} years experience</div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Assigned Site Surveys ({(techSchedule.surveys || []).length})
              </div>
              {(techSchedule.surveys || []).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-light)', padding: '8px', backgroundColor: 'var(--bg-page)', borderRadius: '6px' }}>No pending surveys</div>
              ) : (
                (techSchedule.surveys || []).map((s) => (
                  <div key={s.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', border: '1px solid var(--border-color)', borderRadius: '8px', marginBottom: '6px', fontSize: '13px' }}>
                    <div>
                      <strong>{s.ref}</strong>: {s.customer_name} ({s.address})
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Date: {s.scheduled_date}</div>
                    </div>
                    <StatusBadge status={s.status} />
                  </div>
                ))
              )}
            </div>

            <div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Assigned Installations ({(techSchedule.installations || []).length})
              </div>
              {(techSchedule.installations || []).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-light)', padding: '8px', backgroundColor: 'var(--bg-page)', borderRadius: '6px' }}>No active installations</div>
              ) : (
                (techSchedule.installations || []).map((i) => (
                  <div key={i.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', border: '1px solid var(--border-color)', borderRadius: '8px', marginBottom: '6px', fontSize: '13px' }}>
                    <div>
                      <strong>{i.job_number}</strong>: {i.customer_name} ({i.address})
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Date: {i.scheduled_date}</div>
                    </div>
                    <StatusBadge status={i.status} />
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};



export default TechniciansPage;
