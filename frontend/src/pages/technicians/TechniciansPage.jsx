import React, { useState, useEffect } from 'react';
import { Plus, Wrench, Phone, Mail, Calendar, Link2 } from 'lucide-react';
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
  const [eligibleUsers, setEligibleUsers] = useState([]);
  const [isLinkOpen, setIsLinkOpen] = useState(false);
  const [linkingTech, setLinkingTech] = useState(null);
  const [selectedUserId, setSelectedUserId] = useState('');

  const [newTech, setNewTech] = useState({
    name: '',
    phone: '',
    email: '',
    skills: 'Rooftop Mounts, Inverters, Electrical',
    experience_years: 3,
    availability: 'AVAILABLE',
    employment_status: 'FULL_TIME',
  });

  const fetchTechnicians = async (showLoading = true) => {
    if (showLoading) setLoading(true);
    try {
      const [res, usersRes] = await Promise.all([
        techniciansAPI.getTechnicians(),
        techniciansAPI.getEligibleUsers(),
      ]);
      setTechnicians(res.data);
      setEligibleUsers(usersRes.data);
    } catch (err) {
      console.error('Failed to load technicians:', err);
    } finally {
      if (showLoading) setLoading(false);
    }
  };

  useEffect(() => {
    fetchTechnicians();
    const intervalId = window.setInterval(() => fetchTechnicians(false), 15000);
    return () => window.clearInterval(intervalId);
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

  const openLinkAccount = (tech) => {
    setLinkingTech(tech);
    setSelectedUserId(tech.user_id ? String(tech.user_id) : '');
    setIsLinkOpen(true);
  };

  const handleLinkAccount = async (event) => {
    event.preventDefault();
    try {
      await techniciansAPI.linkUser(
        linkingTech.id,
        selectedUserId ? Number(selectedUserId) : null,
      );
      setIsLinkOpen(false);
      await fetchTechnicians();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to link technician account');
    }
  };

  const linkedElsewhere = new Set(
    technicians
      .filter((tech) => tech.id !== linkingTech?.id && tech.user_id)
      .map((tech) => tech.user_id),
  );

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
      header: 'Login Account',
      render: (row) => {
        const account = eligibleUsers.find((user) => user.id === row.user_id);
        return (
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>{account ? account.email : 'Not linked'}</span>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => openLinkAccount(row)}
              title={`Link a login account to ${row.name}`}
            >
              <Link2 size={13} /> Link
            </button>
          </div>
        );
      },
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
        title={`Field Technician Workforce (${technicians.length} profiles)`}
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

      <Modal
        isOpen={isLinkOpen}
        onClose={() => setIsLinkOpen(false)}
        title={`Link Login Account: ${linkingTech?.name || ''}`}
      >
        <form onSubmit={handleLinkAccount} className="space-y-4">
          <p className="text-sm text-stone-600">
            Link an existing active Solar Technician account. This does not create a login or change its password.
          </p>
          <select
            value={selectedUserId}
            onChange={(event) => setSelectedUserId(event.target.value)}
            className="w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-sm"
          >
            <option value="">No linked account</option>
            {eligibleUsers.map((user) => (
              <option
                key={user.id}
                value={user.id}
                disabled={linkedElsewhere.has(user.id)}
              >
                {user.name} · {user.email}{linkedElsewhere.has(user.id) ? ' (already linked)' : ''}
              </option>
            ))}
          </select>
          <div className="flex justify-end gap-2">
            <button type="button" className="btn btn-secondary" onClick={() => setIsLinkOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Save Link
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
