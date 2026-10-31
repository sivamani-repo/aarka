import React, { useState, useEffect } from 'react';
import { Plus, CheckCircle, Calendar, Phone, Mail, MapPin, UserPlus, FileCheck } from 'lucide-react';
import { leadsAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const LeadsPage = () => {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [stageFilter, setStageFilter] = useState('ALL');

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isQualifyOpen, setIsQualifyOpen] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);

  // Forms
  const [newLead, setNewLead] = useState({
    customer_name: '',
    phone: '',
    email: '',
    address: '',
    city: 'Hyderabad',
    customer_type: 'Residential',
    lead_source: 'Phone',
    required_capacity_kw: 3.0,
    solar_requirement: 'On-Grid',
    monthly_bill: 3000,
    subsidy_required: true,
    notes: '',
  });

  const [qualifyData, setQualifyData] = useState({
    shadow_free_roof_space: '600 sqft Flat RCC Terrace',
    monthly_electricity_bill: 3500,
    grid_suitability: true,
    customer_interest: 'HIGH',
    estimated_opportunity_value: 178000,
    notes: 'Homeowner confirmed terrace ownership and grid connection suitability.',
  });

  const fetchLeads = async () => {
    setLoading(true);
    try {
      const res = await leadsAPI.getLeads({
        stage: stageFilter !== 'ALL' ? stageFilter : undefined,
      });
      setLeads(res.data);
    } catch (err) {
      console.error('Failed to fetch leads:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLeads();
  }, [stageFilter]);

  const handleCreateLead = async (e) => {
    e.preventDefault();
    try {
      await leadsAPI.createLead(newLead);
      setIsCreateOpen(false);
      setNewLead({
        customer_name: '',
        phone: '',
        email: '',
        address: '',
        city: 'Hyderabad',
        customer_type: 'Residential',
        lead_source: 'Phone',
        required_capacity_kw: 3.0,
        solar_requirement: 'On-Grid',
        monthly_bill: 3000,
        subsidy_required: true,
        notes: '',
      });
      fetchLeads();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create lead');
    }
  };

  const handleQualifyLead = async (e) => {
    e.preventDefault();
    if (!selectedLead) return;
    try {
      await leadsAPI.qualifyLead(selectedLead.id, qualifyData);
      setIsQualifyOpen(false);
      setSelectedLead(null);
      fetchLeads();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to qualify lead');
    }
  };

  const columns = [
    {
      header: 'Reference',
      accessor: 'lead_reference',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
          {row.lead_reference}
        </span>
      ),
    },
    {
      header: 'Customer Details',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '600', color: 'var(--text-main)' }}>{row.customer_name}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', gap: '8px', marginTop: '2px' }}>
            <span><Phone size={12} style={{ display: 'inline' }} /> {row.phone}</span>
            <span><MapPin size={12} style={{ display: 'inline' }} /> {row.city}</span>
          </div>
        </div>
      ),
    },
    {
      header: 'Requirement',
      render: (row) => (
        <div>
          <span style={{ fontWeight: '600' }}>{row.required_capacity_kw} kW</span>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}> • {row.solar_requirement}</span>
          <div style={{ fontSize: '11px', color: 'var(--text-light)' }}>
            Bill: ₹{row.monthly_bill?.toLocaleString()}/mo
          </div>
        </div>
      ),
    },
    {
      header: 'Source',
      accessor: 'lead_source',
      render: (row) => <span className="badge badge-neutral">{row.lead_source}</span>,
    },
    {
      header: 'Stage',
      render: (row) => <StatusBadge status={row.stage} />,
    },
    {
      header: 'Opportunity (₹)',
      render: (row) => (
        <span style={{ fontWeight: '700' }}>
          ₹{(row.estimated_value || row.required_capacity_kw * 65000).toLocaleString()}
        </span>
      ),
    },
    {
      header: 'Sales Rep',
      accessor: 'assigned_sales_rep',
      render: (row) => <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{row.assigned_sales_rep || 'Unassigned'}</span>,
    },
    {
      header: 'Actions',
      render: (row) => (
        <div style={{ display: 'flex', gap: '6px' }}>
          {row.stage === 'NEW' || row.stage === 'CONTACTED' ? (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => {
                setSelectedLead(row);
                setQualifyData({
                  shadow_free_roof_space: '600 sqft Flat RCC Terrace',
                  monthly_electricity_bill: row.monthly_bill || 3500,
                  grid_suitability: true,
                  customer_interest: 'HIGH',
                  estimated_opportunity_value: row.required_capacity_kw * 65000,
                  notes: 'Verified monthly electricity bill and south-facing terrace orientation.',
                });
                setIsQualifyOpen(true);
              }}
            >
              <CheckCircle size={14} /> Qualify
            </button>
          ) : (
            <span style={{ fontSize: '12px', color: 'var(--color-primary-600)', fontWeight: '600' }}>
              Qualified ✓
            </span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['ALL', 'NEW', 'CONTACTED', 'QUALIFIED', 'SURVEY_SCHEDULED', 'SURVEY_APPROVED', 'QUOTATION', 'CONVERTED'].map((st) => (
            <button
              key={st}
              className={`btn btn-sm ${stageFilter === st ? 'btn-primary' : 'btn-secondary'}`}
              onClick={() => setStageFilter(st)}
            >
              {st.replace(/_/g, ' ')}
            </button>
          ))}
        </div>

        <button className="btn btn-primary" onClick={() => setIsCreateOpen(true)}>
          <Plus size={16} /> New Customer Lead
        </button>
      </div>

      <DataTable
        title="Customer Leads Pipeline"
        subtitle="Track incoming solar inquiries from first call to site survey scheduling"
        columns={columns}
        data={leads}
        searchKey="customer_name"
        searchPlaceholder="Search leads by customer, phone, reference..."
      />

      {/* Create Lead Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create New Customer Lead">
        <form onSubmit={handleCreateLead}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Customer Name *</label>
              <input
                type="text"
                required
                className="form-control"
                value={newLead.customer_name}
                onChange={(e) => setNewLead({ ...newLead, customer_name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Phone Number *</label>
              <input
                type="tel"
                required
                className="form-control"
                value={newLead.phone}
                onChange={(e) => setNewLead({ ...newLead, phone: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-control"
                value={newLead.email}
                onChange={(e) => setNewLead({ ...newLead, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">City *</label>
              <input
                type="text"
                required
                className="form-control"
                value={newLead.city}
                onChange={(e) => setNewLead({ ...newLead, city: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Full Address *</label>
            <input
              type="text"
              required
              className="form-control"
              value={newLead.address}
              onChange={(e) => setNewLead({ ...newLead, address: e.target.value })}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Required Capacity</label>
              <select
                className="form-select"
                value={newLead.required_capacity_kw}
                onChange={(e) => setNewLead({ ...newLead, required_capacity_kw: parseFloat(e.target.value) })}
              >
                <option value={1.0}>1 kW</option>
                <option value={2.0}>2 kW</option>
                <option value={3.0}>3 kW [Standard]</option>
                <option value={4.0}>4 kW</option>
                <option value={5.0}>5 kW</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Solar Type</label>
              <select
                className="form-select"
                value={newLead.solar_requirement}
                onChange={(e) => setNewLead({ ...newLead, solar_requirement: e.target.value })}
              >
                <option value="On-Grid">On-Grid</option>
                <option value="Off-Grid">Off-Grid</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Lead Source</label>
              <select
                className="form-select"
                value={newLead.lead_source}
                onChange={(e) => setNewLead({ ...newLead, lead_source: e.target.value })}
              >
                <option value="Phone">Phone</option>
                <option value="WhatsApp">WhatsApp</option>
                <option value="Website">Website</option>
                <option value="Referral">Referral</option>
              </select>
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Initial Discussion Notes</label>
            <textarea
              rows={2}
              className="form-textarea"
              value={newLead.notes}
              onChange={(e) => setNewLead({ ...newLead, notes: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Save Lead
            </button>
          </div>
        </form>
      </Modal>

      {/* Qualify Lead Modal */}
      <Modal isOpen={isQualifyOpen} onClose={() => setIsQualifyOpen(false)} title={`Qualify Lead: ${selectedLead?.lead_reference}`}>
        <form onSubmit={handleQualifyLead}>
          <div style={{ backgroundColor: 'var(--color-primary-50)', padding: '12px 16px', borderRadius: 'var(--radius-md)', marginBottom: '16px', fontSize: '13px' }}>
            <strong>Customer:</strong> {selectedLead?.customer_name} ({selectedLead?.phone})<br />
            <strong>System Requested:</strong> {selectedLead?.required_capacity_kw} kW {selectedLead?.solar_requirement}
          </div>

          <div className="form-group">
            <label className="form-label">Shadow-Free Roof Space & Condition *</label>
            <input
              type="text"
              required
              className="form-control"
              placeholder="e.g. 600 sqft RCC Flat Terrace with south orientation"
              value={qualifyData.shadow_free_roof_space}
              onChange={(e) => setQualifyData({ ...qualifyData, shadow_free_roof_space: e.target.value })}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Customer Interest Level</label>
              <select
                className="form-select"
                value={qualifyData.customer_interest}
                onChange={(e) => setQualifyData({ ...qualifyData, customer_interest: e.target.value })}
              >
                <option value="HIGH">High (Immediate Requirement)</option>
                <option value="MEDIUM">Medium (Exploring Quotes)</option>
                <option value="LOW">Low (Information Gathering)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Estimated Deal Value (₹)</label>
              <input
                type="number"
                required
                className="form-control"
                value={qualifyData.estimated_opportunity_value}
                onChange={(e) => setQualifyData({ ...qualifyData, estimated_opportunity_value: parseFloat(e.target.value) || 0 })}
              />
            </div>
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', fontWeight: '600', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={qualifyData.grid_suitability}
                onChange={(e) => setQualifyData({ ...qualifyData, grid_suitability: e.target.checked })}
                style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary-700)' }}
              />
              <span>Grid connection is suitable for Net Metering (DISCOM sanctionable)</span>
            </label>
          </div>

          <div className="form-group">
            <label className="form-label">Sales Representative Qualification Notes</label>
            <textarea
              rows={2}
              className="form-textarea"
              value={qualifyData.notes}
              onChange={(e) => setQualifyData({ ...qualifyData, notes: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsQualifyOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              <CheckCircle size={16} /> Mark as Qualified (Proceed to Survey)
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};



export default LeadsPage;
