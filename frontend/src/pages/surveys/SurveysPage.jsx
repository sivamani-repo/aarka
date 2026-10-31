import React, { useState, useEffect } from 'react';
import { Plus, CheckCircle, XCircle, Camera, Upload, MapPin, Wrench, FileText, Image as ImageIcon } from 'lucide-react';
import { surveysAPI, customersAPI, techniciansAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const SurveysPage = () => {
  const [surveys, setSurveys] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [isUpdateOpen, setIsUpdateOpen] = useState(false);
  const [isApproveOpen, setIsApproveOpen] = useState(false);
  const [selectedSurvey, setSelectedSurvey] = useState(null);

  // Forms
  const [newSurvey, setNewSurvey] = useState({
    customer_id: '',
    technician_id: '',
    scheduled_date: new Date().toISOString().split('T')[0],
    required_capacity_kw: 3.0,
    observations: '',
  });

  const [surveyUpdate, setSurveyUpdate] = useState({
    roof_area: 600,
    shadow_free_area: 550,
    roof_direction: 'South',
    roof_tilt: 18,
    cable_distance: 15,
    structural_condition: 'Good - RCC Flat Concrete Slab',
    grid_connection_suitable: true,
    observations: 'Clean south orientation. No tall buildings nearby. RCC terrace has strong load capacity.',
    technician_recommendation: 'Recommend 3.24kW Mono PERC array with 3.3kW On-Grid string inverter.',
    status: 'SUBMITTED',
  });

  const [approvalAction, setApprovalAction] = useState({
    action: 'APPROVE',
    rejection_reason: '',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [survRes, custRes, techRes] = await Promise.all([
        surveysAPI.getSurveys(),
        customersAPI.getCustomers(),
        techniciansAPI.getTechnicians(),
      ]);
      setSurveys(survRes.data);
      setCustomers(custRes.data);
      setTechnicians(techRes.data);
      if (custRes.data.length > 0) {
        setNewSurvey((prev) => ({ ...prev, customer_id: custRes.data[0].id }));
      }
      if (techRes.data.length > 0) {
        setNewSurvey((prev) => ({ ...prev, technician_id: techRes.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load surveys:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleSchedule = async (e) => {
    e.preventDefault();
    try {
      await surveysAPI.scheduleSurvey({
        ...newSurvey,
        customer_id: parseInt(newSurvey.customer_id),
        technician_id: newSurvey.technician_id ? parseInt(newSurvey.technician_id) : null,
      });
      setIsScheduleOpen(false);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to schedule survey');
    }
  };

  const handleUpdateInspection = async (e) => {
    e.preventDefault();
    if (!selectedSurvey) return;
    try {
      await surveysAPI.updateSurvey(selectedSurvey.id, surveyUpdate);
      setIsUpdateOpen(false);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to update survey');
    }
  };

  const handleApproveOrReject = async (e) => {
    e.preventDefault();
    if (!selectedSurvey) return;
    try {
      await surveysAPI.approveSurvey(selectedSurvey.id, approvalAction);
      setIsApproveOpen(false);
      fetchData();
    } catch (err) {
      alert(err.response?.data?.detail || 'Action failed');
    }
  };

  const columns = [
    {
      header: 'Survey Ref',
      accessor: 'survey_reference',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
          {row.survey_reference}
        </span>
      ),
    },
    {
      header: 'Customer & Site',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '600' }}>{row.customer_name}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            <MapPin size={12} style={{ display: 'inline' }} /> {row.customer_address}
          </div>
        </div>
      ),
    },
    {
      header: 'Assigned Tech',
      accessor: 'technician_name',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Wrench size={13} color="var(--color-primary-600)" />
          <span style={{ fontWeight: '600', fontSize: '13px' }}>{row.technician_name || 'Unassigned'}</span>
        </div>
      ),
    },
    {
      header: 'Roof Data',
      render: (row) => (
        <div style={{ fontSize: '13px' }}>
          <div><strong>{row.roof_area || 0} sqft</strong> ({row.roof_direction || 'South'})</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            Tilt: {row.roof_tilt}° • Cable: {row.cable_distance}m
          </div>
        </div>
      ),
    },
    {
      header: 'Inspection Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Approval State',
      render: (row) => <StatusBadge status={row.approval_status} />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <div style={{ display: 'flex', gap: '6px' }}>
          {row.status === 'SCHEDULED' || row.status === 'IN_PROGRESS' ? (
            <button
              className="btn btn-secondary btn-sm"
              onClick={() => {
                setSelectedSurvey(row);
                setIsUpdateOpen(true);
              }}
            >
              <Camera size={13} /> Mobile Inspect
            </button>
          ) : null}

          {row.approval_status === 'PENDING' && (row.status === 'SUBMITTED' || row.status === 'APPROVED') ? (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => {
                setSelectedSurvey(row);
                setApprovalAction({ action: 'APPROVE', rejection_reason: '' });
                setIsApproveOpen(true);
              }}
            >
              <CheckCircle size={13} /> Review & Approve
            </button>
          ) : null}

          {row.approval_status === 'APPROVED' && (
            <span style={{ fontSize: '12px', color: 'var(--color-primary-600)', fontWeight: '700' }}>
              Approved ✓
            </span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <button className="btn btn-primary" onClick={() => setIsScheduleOpen(true)}>
          <Plus size={16} /> Schedule Site Inspection
        </button>
      </div>

      <DataTable
        title="Site Survey & Roof Inspections"
        subtitle="MANDATORY RULE: Survey must be approved by engineering before quotation finalization"
        columns={columns}
        data={surveys}
        searchKey="survey_reference"
        searchPlaceholder="Search surveys by reference, customer, technician..."
      />

      {/* Schedule Survey Modal */}
      <Modal isOpen={isScheduleOpen} onClose={() => setIsScheduleOpen(false)} title="Schedule Rooftop Site Survey">
        <form onSubmit={handleSchedule}>
          <div className="form-group">
            <label className="form-label">Select Customer *</label>
            <select
              className="form-select"
              required
              value={newSurvey.customer_id}
              onChange={(e) => setNewSurvey({ ...newSurvey, customer_id: e.target.value })}
            >
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.phone}) - {c.address}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Assign Technician</label>
              <select
                className="form-select"
                value={newSurvey.technician_id}
                onChange={(e) => setNewSurvey({ ...newSurvey, technician_id: e.target.value })}
              >
                {technicians.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.skills})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Survey Scheduled Date *</label>
              <input
                type="date"
                required
                className="form-control"
                value={newSurvey.scheduled_date}
                onChange={(e) => setNewSurvey({ ...newSurvey, scheduled_date: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Initial Inspection Instructions</label>
            <textarea
              rows={2}
              className="form-textarea"
              placeholder="Check shading from nearby water tanks, roof tilt, and meter box distance"
              value={newSurvey.observations}
              onChange={(e) => setNewSurvey({ ...newSurvey, observations: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsScheduleOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Confirm Survey Schedule
            </button>
          </div>
        </form>
      </Modal>

      {/* Mobile Technician Inspection Update Modal */}
      <Modal isOpen={isUpdateOpen} onClose={() => setIsUpdateOpen(false)} title={`Technician Mobile Survey Form: ${selectedSurvey?.survey_reference}`} maxWidth="750px">
        <form onSubmit={handleUpdateInspection}>
          <div style={{ backgroundColor: 'var(--color-primary-50)', padding: '12px 16px', borderRadius: 'var(--radius-md)', marginBottom: '16px', fontSize: '13px' }}>
            <strong>Customer:</strong> {selectedSurvey?.customer_name}<br />
            <strong>Address:</strong> {selectedSurvey?.customer_address}
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Total Roof Area (sqft) *</label>
              <input
                type="number"
                required
                className="form-control"
                value={surveyUpdate.roof_area}
                onChange={(e) => setSurveyUpdate({ ...surveyUpdate, roof_area: parseFloat(e.target.value) || 0 })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Shadow-Free Usable Area (sqft) *</label>
              <input
                type="number"
                required
                className="form-control"
                value={surveyUpdate.shadow_free_area}
                onChange={(e) => setSurveyUpdate({ ...surveyUpdate, shadow_free_area: parseFloat(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Roof Orientation</label>
              <select
                className="form-select"
                value={surveyUpdate.roof_direction}
                onChange={(e) => setSurveyUpdate({ ...surveyUpdate, roof_direction: e.target.value })}
              >
                <option value="South">South (Optimal)</option>
                <option value="South-West">South-West</option>
                <option value="South-East">South-East</option>
                <option value="West">West</option>
                <option value="East">East</option>
                <option value="North">North (Not Recommended)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Roof Tilt (°)</label>
              <input
                type="number"
                className="form-control"
                value={surveyUpdate.roof_tilt}
                onChange={(e) => setSurveyUpdate({ ...surveyUpdate, roof_tilt: parseFloat(e.target.value) || 0 })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Cable Distance to Meter (m)</label>
              <input
                type="number"
                className="form-control"
                value={surveyUpdate.cable_distance}
                onChange={(e) => setSurveyUpdate({ ...surveyUpdate, cable_distance: parseFloat(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Structural Condition</label>
            <input
              type="text"
              className="form-control"
              value={surveyUpdate.structural_condition}
              onChange={(e) => setSurveyUpdate({ ...surveyUpdate, structural_condition: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Technical Observations</label>
            <textarea
              rows={2}
              className="form-textarea"
              value={surveyUpdate.observations}
              onChange={(e) => setSurveyUpdate({ ...surveyUpdate, observations: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Technician Recommendation</label>
            <textarea
              rows={2}
              className="form-textarea"
              value={surveyUpdate.technician_recommendation}
              onChange={(e) => setSurveyUpdate({ ...surveyUpdate, technician_recommendation: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsUpdateOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Submit Survey Data (Ready for Review)
            </button>
          </div>
        </form>
      </Modal>

      {/* Review & Approve / Reject Modal */}
      <Modal isOpen={isApproveOpen} onClose={() => setIsApproveOpen(false)} title={`Engineering Review: ${selectedSurvey?.survey_reference}`}>
        <form onSubmit={handleApproveOrReject}>
          <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '14px', borderRadius: 'var(--radius-md)', marginBottom: '16px', fontSize: '13px' }}>
            <div><strong>Customer:</strong> {selectedSurvey?.customer_name}</div>
            <div><strong>Observations:</strong> {selectedSurvey?.observations || 'Terrace inspected and verified.'}</div>
            <div><strong>Recommendation:</strong> {selectedSurvey?.technician_recommendation || 'Standard 3kW On-grid configuration suitable.'}</div>
          </div>

          <div className="form-group">
            <label className="form-label">Decision Action *</label>
            <select
              className="form-select"
              value={approvalAction.action}
              onChange={(e) => setApprovalAction({ ...approvalAction, action: e.target.value })}
            >
              <option value="APPROVE">✓ Approve Survey (Authorize Quotation Generation)</option>
              <option value="REJECT">✗ Reject Survey (Requires Reason)</option>
            </select>
          </div>

          {approvalAction.action === 'REJECT' && (
            <div className="form-group">
              <label className="form-label">Rejection Reason *</label>
              <textarea
                rows={2}
                required
                className="form-textarea"
                placeholder="Specify structural or electrical defect preventing installation"
                value={approvalAction.rejection_reason}
                onChange={(e) => setApprovalAction({ ...approvalAction, rejection_reason: e.target.value })}
              />
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsApproveOpen(false)}>
              Cancel
            </button>
            <button
              type="submit"
              className={`btn ${approvalAction.action === 'APPROVE' ? 'btn-primary' : 'btn-danger'}`}
            >
              Confirm {approvalAction.action === 'APPROVE' ? 'Approval' : 'Rejection'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};



export default SurveysPage;
