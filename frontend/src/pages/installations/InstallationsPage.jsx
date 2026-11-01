import React, { useState, useEffect } from 'react';
import { Plus, Zap, CheckCircle, Wrench, MapPin, Eye, Camera, PenTool, AlertCircle } from 'lucide-react';
import { installationsAPI, ordersAPI, techniciansAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';
import { SignatureCanvas } from '../../components/common/SignatureCanvas';

export const InstallationsPage = () => {
  const [installations, setInstallations] = useState([]);
  const [confirmedOrders, setConfirmedOrders] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isScheduleOpen, setIsScheduleOpen] = useState(false);
  const [isExecuteOpen, setIsExecuteOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState(null);

  // Form
  const [newSchedule, setNewSchedule] = useState({
    order_id: '',
    technician_id: '',
    scheduled_date: new Date().toISOString().split('T')[0],
    capacity_kw: 3.0,
  });

  // Mobile Execution State (9 Checklist Points)
  const [checklist, setChecklist] = useState({
    mounting_inspected: false,
    panels_installed: false,
    inverter_installed: false,
    wiring_completed: false,
    earthing_completed: false,
    safety_checked: false,
    system_tested: false,
    power_verified: false,
    customer_handover: false,
  });

  const [technicalObservations, setTechnicalObservations] = useState(
    'All modules aligned to 18° tilt south facing. Inverter MPPT efficiency 98.4%. Earthing resistance measured at 1.8 ohms.'
  );
  const [testingResults, setTestingResults] = useState(
    'Grid voltage 238V, frequency 50.1Hz, DC isolation OK, solar generation verified at 3.1kW.'
  );
  const [signatureData, setSignatureData] = useState('');
  const [submitError, setSubmitError] = useState('');

  const checklistItems = [
    { id: 'mounting_inspected', label: '1. Mounting structure inspected and anchored to roof slab' },
    { id: 'panels_installed', label: '2. Solar PV modules installed, aligned, and clamped securely' },
    { id: 'inverter_installed', label: '3. Inverter wall-mounted in shade with ventilation clearance' },
    { id: 'wiring_completed', label: '4. DC solar cables & AC conduit wiring neatly routed and terminated' },
    { id: 'earthing_completed', label: '5. Chemical earthing pits and lightning arrester connected' },
    { id: 'safety_checked', label: '6. ACDB & DCDB surge protective devices and MCBs tested' },
    { id: 'system_tested', label: '7. Open circuit voltage (Voc) & short circuit current (Isc) tested' },
    { id: 'power_verified', label: '8. Power generation verified on bi-directional / generation meter' },
    { id: 'customer_handover', label: '9. Customer handover completed, system briefing & app monitoring configured' },
  ];

  const fetchData = async () => {
    setLoading(true);
    try {
      const [instRes, ordRes, techRes] = await Promise.all([
        installationsAPI.getInstallations(),
        ordersAPI.getOrders(),
        techniciansAPI.getTechnicians(),
      ]);
      setInstallations(instRes.data);
      setConfirmedOrders(ordRes.data);
      setTechnicians(techRes.data);
      if (ordRes.data.length > 0) {
        setNewSchedule((prev) => ({ ...prev, order_id: ordRes.data[0].id }));
      }
      if (techRes.data.length > 0) {
        setNewSchedule((prev) => ({ ...prev, technician_id: techRes.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load installations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const openExecutionModal = (job) => {
    setSelectedJob(job);
    let st = {};
    try {
      st = JSON.parse(job.checklist_state || '{}');
    } catch (e) {
      st = {};
    }
    setChecklist({
      mounting_inspected: !!st.mounting_inspected,
      panels_installed: !!st.panels_installed,
      inverter_installed: !!st.inverter_installed,
      wiring_completed: !!st.wiring_completed,
      earthing_completed: !!st.earthing_completed,
      safety_checked: !!st.safety_checked,
      system_tested: !!st.system_tested,
      power_verified: !!st.power_verified,
      customer_handover: !!st.customer_handover,
    });
    setTechnicalObservations(job.technical_observations || technicalObservations);
    setTestingResults(job.testing_results || testingResults);
    setSignatureData(job.customer_signature || '');
    setSubmitError('');
    setIsExecuteOpen(true);
  };

  const handleScheduleJob = async (e) => {
    e.preventDefault();
    try {
      await installationsAPI.scheduleInstallation({
        order_id: parseInt(newSchedule.order_id),
        technician_id: parseInt(newSchedule.technician_id),
        scheduled_date: newSchedule.scheduled_date,
        capacity_kw: parseFloat(newSchedule.capacity_kw),
      });
      setIsScheduleOpen(false);
      fetchData();
      alert('Installation scheduled successfully.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to schedule installation');
    }
  };

  const handleCompleteHandover = async (e) => {
    e.preventDefault();
    setSubmitError('');

    // Rule #13: Verify all 9 items checked
    const missing = checklistItems.filter((item) => !checklist[item.id]);
    if (missing.length > 0) {
      setSubmitError(`Cannot complete handover: ${missing.length} checklist items still incomplete.`);
      return;
    }

    // Rule #14: Verify signature captured
    if (!signatureData) {
      setSubmitError('Customer electronic signature is mandatory for project acceptance and handover.');
      return;
    }

    try {
      await installationsAPI.completeInstallation(selectedJob.id, {
        checklist_state: checklist,
        technical_observations: technicalObservations,
        testing_results: testingResults,
        customer_signature: signatureData,
        labour_hours: 6.0,
      });

      setIsExecuteOpen(false);
      fetchData();
      alert(`✓ Installation ${selectedJob.job_number} successfully completed and accepted by customer!`);
    } catch (err) {
      setSubmitError(err.response?.data?.detail || 'Failed to complete installation');
    }
  };

  const allChecked = checklistItems.every((item) => checklist[item.id]);

  const columns = [
    {
      header: 'Job Number',
      accessor: 'job_number',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
          {row.job_number}
        </span>
      ),
    },
    {
      header: 'Order & Customer',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '700' }}>{row.customer_name}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Order: {row.order_number} • {row.capacity_kw} kW
          </div>
        </div>
      ),
    },
    {
      header: 'Lead Technician',
      accessor: 'technician_name',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Wrench size={14} color="var(--color-primary-600)" />
          <span style={{ fontWeight: '600' }}>{row.technician_name || 'Unassigned'}</span>
        </div>
      ),
    },
    {
      header: 'Scheduled Date',
      accessor: 'scheduled_date',
    },
    {
      header: 'Handover Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Testing Results',
      accessor: 'testing_results',
      render: (row) => (
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '240px', display: 'inline-block' }}>
          {row.testing_results || 'Pending'}
        </span>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            className={`btn btn-sm ${row.status === 'CUSTOMER_ACCEPTED' ? 'btn-secondary' : 'btn-primary'}`}
            onClick={() => openExecutionModal(row)}
          >
            {row.status === 'CUSTOMER_ACCEPTED' ? <Eye size={13} /> : <PenTool size={13} />}
            {row.status === 'CUSTOMER_ACCEPTED' ? 'View Handover' : 'Mobile Checklist'}
          </button>
        </div>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <button className="btn btn-primary" onClick={() => setIsScheduleOpen(true)}>
          <Plus size={16} /> Schedule Installation Job
        </button>
      </div>

      <DataTable
        title="Field Installation Operations & Handover"
        subtitle="MANDATORY RULES #13 & #14: Enforces 9-point technical checklist, power generation verification, and customer signature canvas"
        columns={columns}
        data={installations}
        searchKey="job_number"
        searchPlaceholder="Search installations by job number, customer..."
      />

      {/* Schedule Installation Modal */}
      <Modal isOpen={isScheduleOpen} onClose={() => setIsScheduleOpen(false)} title="Schedule Field Installation Job">
        <form onSubmit={handleScheduleJob}>
          <div className="form-group">
            <label className="form-label">Sales Order *</label>
            <select
              className="form-select"
              required
              value={newSchedule.order_id}
              onChange={(e) => {
                const oId = e.target.value;
                const ord = confirmedOrders.find((o) => o.id === parseInt(oId));
                setNewSchedule({
                  ...newSchedule,
                  order_id: oId,
                  capacity_kw: ord ? ord.capacity_kw : 3.0,
                });
              }}
            >
              {confirmedOrders.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.order_number} - {o.customer_name} ({o.capacity_kw}kW {o.package_type})
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Lead Installation Technician *</label>
              <select
                className="form-select"
                required
                value={newSchedule.technician_id}
                onChange={(e) => setNewSchedule({ ...newSchedule, technician_id: e.target.value })}
              >
                {technicians.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.name} ({t.skills})
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Scheduled Date *</label>
              <input
                type="date"
                required
                className="form-control"
                value={newSchedule.scheduled_date}
                onChange={(e) => setNewSchedule({ ...newSchedule, scheduled_date: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsScheduleOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Schedule Deployment
            </button>
          </div>
        </form>
      </Modal>

      {/* Mobile Execution & Customer Handover Modal */}
      <Modal isOpen={isExecuteOpen} onClose={() => setIsExecuteOpen(false)} title={`Field Installation Handover: ${selectedJob?.job_number}`} maxWidth="850px">
        {selectedJob && (
          <div>
            <div style={{ backgroundColor: 'var(--color-primary-50)', padding: '14px 18px', borderRadius: '8px', marginBottom: '20px', fontSize: '13px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <strong>Customer:</strong> {selectedJob.customer_name} ({selectedJob.customer_phone})<br />
                  <strong>Site:</strong> {selectedJob.customer_address}
                </div>
                <div>
                  <strong>System:</strong> {selectedJob.capacity_kw} kW Solar Array<br />
                  <strong>Lead Tech:</strong> {selectedJob.technician_name}
                </div>
              </div>
            </div>

            {submitError && (
              <div style={{ padding: '12px', backgroundColor: 'var(--color-rose-50)', color: 'var(--color-rose-600)', borderRadius: '8px', marginBottom: '16px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} />
                <span>{submitError}</span>
              </div>
            )}

            {/* 9 Mandatory Checklist Items */}
            <div style={{ marginBottom: '24px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                <h4 style={{ fontSize: '14px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)' }}>
                  Mandatory 9-Point Commissioning Checklist (Rule #13)
                </h4>
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={() => {
                    const allTrue = {};
                    checklistItems.forEach((it) => (allTrue[it.id] = true));
                    setChecklist(allTrue);
                  }}
                >
                  ✓ Check All 9 Items
                </button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {checklistItems.map((item) => (
                  <label
                    key={item.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '10px 14px',
                      backgroundColor: checklist[item.id] ? 'var(--color-primary-50)' : 'var(--bg-subtle)',
                      borderRadius: '8px',
                      cursor: 'pointer',
                      border: checklist[item.id] ? '1px solid var(--color-primary-200)' : '1px solid transparent',
                      transition: 'all 0.15s ease',
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={checklist[item.id]}
                      onChange={(e) => setChecklist({ ...checklist, [item.id]: e.target.checked })}
                      style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary-700)' }}
                    />
                    <span style={{ fontSize: '13px', fontWeight: checklist[item.id] ? '600' : '400', color: checklist[item.id] ? 'var(--color-primary-900)' : 'var(--text-main)' }}>
                      {item.label}
                    </span>
                  </label>
                ))}
              </div>
            </div>

            {/* Technical Observations & Testing Results */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '24px' }}>
              <div className="form-group">
                <label className="form-label">Technical Observations</label>
                <textarea
                  rows={3}
                  className="form-textarea"
                  value={technicalObservations}
                  onChange={(e) => setTechnicalObservations(e.target.value)}
                />
              </div>

              <div className="form-group">
                <label className="form-label">Power & Meter Testing Results</label>
                <textarea
                  rows={3}
                  className="form-textarea"
                  value={testingResults}
                  onChange={(e) => setTestingResults(e.target.value)}
                />
              </div>
            </div>

            {/* Electronic Customer Signature Canvas (Rule #14) */}
            <div style={{ marginBottom: '24px', borderTop: '1px solid var(--border-color)', paddingTop: '16px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                <label className="form-label" style={{ marginBottom: 0 }}>
                  Customer Handover Acceptance & Electronic Signature (Rule #14) *
                </label>
                {signatureData && (
                  <span style={{ fontSize: '12px', color: 'var(--color-primary-600)', fontWeight: '700' }}>
                    ✓ Signature Captured
                  </span>
                )}
              </div>

              {selectedJob.customer_signature ? (
                <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
                  <img
                    src={selectedJob.customer_signature}
                    alt="Customer Signature"
                    style={{ maxHeight: '100px', margin: '0 auto', border: '1px solid var(--border-color)', borderRadius: '6px', backgroundColor: '#ffffff' }}
                  />
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
                    Signed by {selectedJob.customer_name} • Accepted on Handover
                  </div>
                </div>
              ) : (
                <SignatureCanvas
                  onSave={(dataUrl) => setSignatureData(dataUrl)}
                  onClear={() => setSignatureData('')}
                />
              )}
            </div>

            {/* Complete Handover Button */}
            {selectedJob.status !== 'CUSTOMER_ACCEPTED' && (
              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setIsExecuteOpen(false)}>
                  Cancel
                </button>
                <button
                  type="button"
                  className="btn btn-primary btn-lg"
                  disabled={!allChecked || !signatureData}
                  onClick={handleCompleteHandover}
                >
                  <CheckCircle size={18} /> Complete Installation & Handover to Customer
                </button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};



export default InstallationsPage;
