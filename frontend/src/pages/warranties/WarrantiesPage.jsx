import React, { useState, useEffect, useMemo } from 'react';
import {
  ShieldCheck,
  AlertCircle,
  Clock,
  CheckCircle,
  Barcode,
  Calendar,
  Search,
  Plus,
  FileText,
  Printer,
  AlertTriangle,
  RefreshCw,
  Wrench,
  Check,
  ChevronRight,
  Send,
  Building2,
  ExternalLink,
  SlidersHorizontal,
  Download
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  PieChart,
  Pie,
  Cell
} from 'recharts';
import { warrantiesAPI, techniciansAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';
import { StatCard } from '../../components/common/StatCard';

const PALETTE = ['#047857', '#0284c7', '#d97706', '#7c3aed', '#dc2626', '#059669'];

export const WarrantiesPage = () => {
  const [activeTab, setActiveTab] = useState('OVERVIEW'); // OVERVIEW | ALL_WARRANTIES | EXPIRING | CLAIMS | VERIFY
  const [warranties, setWarranties] = useState([]);
  const [summary, setSummary] = useState(null);
  const [claims, setClaims] = useState([]);
  const [alerts, setAlerts] = useState(null);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [feedback, setFeedback] = useState(null);

  // Filters for All Warranties
  const [typeFilter, setTypeFilter] = useState('ALL');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [searchFilter, setSearchFilter] = useState('');

  // Modals
  const [certificateModal, setCertificateModal] = useState({ open: false, data: null, loading: false });
  const [claimModal, setClaimModal] = useState({ open: false, warranty: null });
  const [claimForm, setClaimForm] = useState({
    issue_description: '',
    manufacturer_reference: '',
    assigned_technician_id: '',
    supporting_documents: []
  });

  const [claimStatusModal, setClaimStatusModal] = useState({ open: false, claim: null });
  const [claimStatusForm, setClaimStatusForm] = useState({
    claim_status: 'UNDER_REVIEW',
    manufacturer_reference: '',
    replacement_serial_number: '',
    resolution_details: ''
  });

  // Quick Verification Tool
  const [quickQuery, setQuickQuery] = useState('');
  const [quickResult, setQuickResult] = useState(null);
  const [quickLoading, setQuickLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [wRes, sRes, cRes, aRes, tRes] = await Promise.all([
        warrantiesAPI.getWarranties(),
        warrantiesAPI.getDashboardSummary(),
        warrantiesAPI.getClaims(),
        warrantiesAPI.getExpiryAlerts(),
        techniciansAPI.getTechnicians ? techniciansAPI.getTechnicians() : Promise.resolve({ data: [] })
      ]);
      setWarranties(wRes.data || []);
      setSummary(sRes.data || null);
      setClaims(cRes.data || []);
      setAlerts(aRes.data || null);
      setTechnicians(tRes.data || []);
    } catch (err) {
      console.error('Failed to load warranty module data:', err);
      setFeedback({ type: 'error', message: 'Failed to load warranty data from server.' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Filtered Warranties
  const filteredWarranties = useMemo(() => {
    return warranties.filter((w) => {
      if (typeFilter !== 'ALL' && w.warranty_type !== typeFilter) return false;
      if (statusFilter !== 'ALL' && w.status !== statusFilter) return false;
      if (searchFilter.trim()) {
        const q = searchFilter.toLowerCase();
        const sn = (w.serial_number || '').toLowerCase();
        const wn = (w.warranty_number || '').toLowerCase();
        const cn = (w.customer_name || '').toLowerCase();
        const pn = (w.product_name || '').toLowerCase();
        if (!sn.includes(q) && !wn.includes(q) && !cn.includes(q) && !pn.includes(q)) return false;
      }
      return true;
    });
  }, [warranties, typeFilter, statusFilter, searchFilter]);

  // Handle Certificate View
  const handleOpenCertificate = async (warranty) => {
    setCertificateModal({ open: true, data: null, loading: true });
    try {
      const res = await warrantiesAPI.getCertificate(warranty.id);
      setCertificateModal({ open: true, data: res.data, loading: false });
    } catch (err) {
      console.error('Failed to load certificate:', err);
      setCertificateModal({ open: false, data: null, loading: false });
      setFeedback({ type: 'error', message: 'Could not generate certificate details.' });
    }
  };

  // Handle Trigger Expiry Alerts
  const handleTriggerAlerts = async () => {
    setActionLoading(true);
    try {
      const res = await warrantiesAPI.triggerExpiryAlerts();
      setFeedback({ type: 'success', message: res.data.message || 'Expiry alerts dispatched successfully!' });
      fetchData();
    } catch (err) {
      setFeedback({ type: 'error', message: 'Failed to trigger expiry alerts.' });
    } finally {
      setActionLoading(false);
    }
  };

  // Handle Quick Verification Search
  const handleQuickVerify = async (e) => {
    e.preventDefault();
    if (!quickQuery.trim()) {
      setQuickResult(null);
      return;
    }
    setQuickLoading(true);
    try {
      const res = await warrantiesAPI.searchWarranties(quickQuery.trim());
      setQuickResult(res.data);
    } catch (err) {
      console.error('Quick verify search error:', err);
      setQuickResult({ results: [] });
    } finally {
      setQuickLoading(false);
    }
  };

  // Submit Claim
  const handleSubmitClaim = async (e) => {
    e.preventDefault();
    if (!claimModal.warranty) return;
    setActionLoading(true);
    try {
      await warrantiesAPI.createClaim({
        warranty_id: claimModal.warranty.id,
        issue_description: claimForm.issue_description,
        manufacturer_reference: claimForm.manufacturer_reference || null,
        assigned_technician_id: claimForm.assigned_technician_id ? parseInt(claimForm.assigned_technician_id) : null,
        supporting_documents: claimForm.supporting_documents
      });
      setFeedback({ type: 'success', message: `Warranty claim successfully lodged against Serial #${claimModal.warranty.serial_number}!` });
      setClaimModal({ open: false, warranty: null });
      setClaimForm({ issue_description: '', manufacturer_reference: '', assigned_technician_id: '', supporting_documents: [] });
      fetchData();
    } catch (err) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to submit warranty claim.' });
    } finally {
      setActionLoading(false);
    }
  };

  // Update Claim Status
  const handleUpdateClaimStatus = async (e) => {
    e.preventDefault();
    if (!claimStatusModal.claim) return;
    setActionLoading(true);
    try {
      await warrantiesAPI.updateClaimStatus(claimStatusModal.claim.id, claimStatusForm);
      setFeedback({ type: 'success', message: `Claim #${claimStatusModal.claim.claim_number} updated to ${claimStatusForm.claim_status}!` });
      setClaimStatusModal({ open: false, claim: null });
      fetchData();
    } catch (err) {
      setFeedback({ type: 'error', message: err.response?.data?.detail || 'Failed to update claim status.' });
    } finally {
      setActionLoading(false);
    }
  };

  const warrantyColumns = [
    {
      header: 'Certificate #',
      accessor: 'warranty_number',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)', fontSize: '13px' }}>
          {row.warranty_number || 'WAR-AUTO'}
        </span>
      ),
    },
    {
      header: 'Serial & Equipment',
      render: (row) => (
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontWeight: '700', color: '#163827' }}>
            <Barcode size={13} color="var(--color-amber-600)" />
            <span>{row.serial_number}</span>
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.product_name}</div>
        </div>
      ),
    },
    {
      header: 'Warranty Type',
      render: (row) => {
        const t = row.warranty_type || 'PRODUCT';
        const colorMap = {
          PRODUCT: { bg: '#e0f2fe', text: '#0369a1' },
          PERFORMANCE: { bg: '#dcfce7', text: '#15803d' },
          WORKMANSHIP: { bg: '#fef3c7', text: '#b45309' },
        };
        const conf = colorMap[t] || { bg: '#f3f4f6', text: '#4b5563' };
        return (
          <span style={{ backgroundColor: conf.bg, color: conf.text, padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '700' }}>
            {t}
          </span>
        );
      },
    },
    {
      header: 'Customer & Project',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '600' }}>{row.customer_name || 'Customer'}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
            {row.order_number ? `Order: ${row.order_number}` : row.customer_phone || ''}
          </div>
        </div>
      ),
    },
    {
      header: 'Active Period',
      render: (row) => (
        <div style={{ fontSize: '12px' }}>
          <div><strong>Start:</strong> {row.warranty_start}</div>
          <div style={{ color: 'var(--text-muted)' }}><strong>Expires:</strong> {row.warranty_end}</div>
        </div>
      ),
    },
    {
      header: 'Days Left',
      render: (row) => {
        const days = row.days_remaining;
        let color = '#15803d';
        if (days <= 0) color = '#dc2626';
        else if (days <= 30) color = '#ea580c';
        else if (days <= 90) color = '#d97706';
        return (
          <span style={{ fontWeight: '700', color, fontSize: '12px' }}>
            {days <= 0 ? 'Expired' : `${days} days`}
          </span>
        );
      },
    },
    {
      header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <div style={{ display: 'flex', gap: '6px' }}>
          <button
            onClick={() => handleOpenCertificate(row)}
            className="btn btn-secondary"
            style={{ padding: '4px 8px', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
            title="View Official Certificate"
          >
            <FileText size={12} /> Certificate
          </button>
          <button
            onClick={() => setClaimModal({ open: true, warranty: row })}
            className="btn btn-secondary"
            style={{ padding: '4px 8px', fontSize: '11px', display: 'inline-flex', alignItems: 'center', gap: '4px', borderColor: '#fca5a5', color: '#991b1b' }}
            title="Raise Warranty Claim"
          >
            <AlertCircle size={12} /> Claim
          </button>
        </div>
      ),
    },
  ];

  const claimColumns = [
    {
      header: 'Claim Ref',
      accessor: 'claim_number',
      render: (row) => <strong style={{ color: '#0c2318' }}>{row.claim_number}</strong>,
    },
    {
      header: 'Equipment & Serial',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '600' }}>{row.equipment_name || 'Equipment'}</div>
          <div style={{ fontSize: '12px', color: 'var(--color-amber-700)', fontFamily: 'monospace' }}>
            {row.serial_number}
          </div>
        </div>
      ),
    },
    {
      header: 'Customer',
      accessor: 'customer_name',
    },
    {
      header: 'OEM Reference',
      render: (row) => (
        <span style={{ fontSize: '12px', fontFamily: 'monospace', color: 'var(--text-muted)' }}>
          {row.manufacturer_reference || 'Awaiting RMA'}
        </span>
      ),
    },
    {
      header: 'Assigned Field Tech',
      render: (row) => row.assigned_technician_name || <em style={{ color: '#9ca3af' }}>Unassigned</em>,
    },
    {
      header: 'Claim Status',
      render: (row) => <StatusBadge status={row.claim_status} />,
    },
    {
      header: 'Action',
      render: (row) => (
        <button
          onClick={() => {
            setClaimStatusModal({ open: true, claim: row });
            setClaimStatusForm({
              claim_status: row.claim_status,
              manufacturer_reference: row.manufacturer_reference || '',
              replacement_serial_number: row.replacement_serial_number || '',
              resolution_details: row.resolution_details || ''
            });
          }}
          className="btn btn-secondary"
          style={{ padding: '4px 10px', fontSize: '12px' }}
        >
          Update Stage
        </button>
      ),
    },
  ];

  return (
    <div>
      {/* Page Title & Navigation Tabs */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <div>
          <h1 style={{ fontSize: '24px', fontWeight: '800', color: 'var(--color-primary-950)', margin: 0, fontFamily: 'var(--font-display)' }}>
            Equipment Warranty Assurance & Lifecycle Desk
          </h1>
          <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: '4px 0 0 0' }}>
            Automated equipment warranty activation on installation completion • Separate product & performance terms • OEM RMA Claims
          </p>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            onClick={fetchData}
            className="btn btn-secondary"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            disabled={loading}
          >
            <RefreshCw size={14} className={loading ? 'animate-spin' : ''} /> Refresh
          </button>
          <button
            onClick={handleTriggerAlerts}
            className="btn btn-accent"
            style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
            disabled={actionLoading}
          >
            <Send size={14} /> Send Expiry Alerts
          </button>
        </div>
      </div>

      {/* Feedback Toast */}
      {feedback && (
        <div
          style={{
            padding: '12px 16px',
            marginBottom: '16px',
            borderRadius: 'var(--radius-md)',
            backgroundColor: feedback.type === 'error' ? '#fef2f2' : '#f0fdf4',
            border: `1px solid ${feedback.type === 'error' ? '#fca5a5' : '#86efac'}`,
            color: feedback.type === 'error' ? '#991b1b' : '#166534',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '13px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {feedback.type === 'error' ? <AlertCircle size={16} /> : <CheckCircle size={16} />}
            <span>{feedback.message}</span>
          </div>
          <button
            onClick={() => setFeedback(null)}
            style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', fontWeight: '700' }}
          >
            ✕
          </button>
        </div>
      )}

      {/* Navigation Tab Bar */}
      <div style={{ display: 'flex', gap: '8px', borderBottom: '1px solid var(--border-color)', marginBottom: '20px' }}>
        {[
          { id: 'OVERVIEW', label: 'Warranty Dashboard & Analytics', icon: ShieldCheck },
          { id: 'ALL_WARRANTIES', label: `Registered Warranties (${warranties.length})`, icon: FileText },
          { id: 'EXPIRING', label: `Expiring Soon (${alerts?.total_expiring_soon || 0})`, icon: Clock },
          { id: 'CLAIMS', label: `Claims & OEM RMA (${claims.length})`, icon: AlertTriangle },
          { id: 'VERIFY', label: 'Instant Serial Verification Tool', icon: Barcode },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
                border: 'none',
                background: 'none',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: isActive ? '700' : '500',
                color: isActive ? 'var(--color-primary-800)' : 'var(--text-muted)',
                borderBottom: isActive ? '3px solid var(--color-primary-800)' : '3px solid transparent',
                transition: 'var(--transition-fast)',
              }}
            >
              <Icon size={16} />
              {tab.label}
            </button>
          );
        })}
      </div>

      {/* TAB 1: OVERVIEW & DASHBOARD */}
      {activeTab === 'OVERVIEW' && (
        <div>
          {/* KPI Stat Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(210px, 1fr))', gap: '14px', marginBottom: '24px' }}>
            <StatCard
              title="Total Warranties"
              value={summary?.total_warranties || warranties.length}
              icon={ShieldCheck}
              trend="All activated certificates"
              variant="default"
            />
            <StatCard
              title="Active & Covered"
              value={summary?.active_warranties || 0}
              icon={CheckCircle}
              trend="In active guarantee"
              variant="success"
            />
            <StatCard
              title="Expiring Within 90d"
              value={summary?.expiring_soon_count || 0}
              icon={Clock}
              trend="Eligible for AMC extension"
              variant="warning"
            />
            <StatCard
              title="Expired Warranties"
              value={summary?.expired_count || 0}
              icon={AlertCircle}
              trend="Past guarantee duration"
              variant="neutral"
            />
            <StatCard
              title="Open Warranty Claims"
              value={summary?.open_claims_count || claims.length}
              icon={AlertTriangle}
              trend="Active OEM RMA tickets"
              variant="danger"
            />
          </div>

          {/* Charts Row */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
            {/* Equipment Distribution BarChart */}
            <div className="aarka-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--color-primary-950)', margin: 0 }}>
                    Warranty Distribution by Equipment Category
                  </h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                    Active warranties across Solar Panels, Inverters, Batteries, Structures & Workmanship
                  </p>
                </div>
              </div>
              <div style={{ width: '100%', height: '240px' }}>
                {summary?.distribution_by_equipment && summary.distribution_by_equipment.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={summary.distribution_by_equipment} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                      <XAxis dataKey="name" angle={-15} textAnchor="end" interval={0} tick={{ fontSize: 11, fill: '#4b5563' }} />
                      <YAxis tick={{ fontSize: 11, fill: '#4b5563' }} />
                      <Tooltip />
                      <Bar dataKey="count" fill="var(--color-primary-800)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', fontSize: '13px' }}>
                    No warranty equipment records to display
                  </div>
                )}
              </div>
            </div>

            {/* 12-Month Expiry Timeline */}
            <div className="aarka-card" style={{ padding: '20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                <div>
                  <h3 style={{ fontSize: '15px', fontWeight: '700', color: 'var(--color-primary-950)', margin: 0 }}>
                    Upcoming Expiry Timeline (Next 12 Months)
                  </h3>
                  <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                    Anticipated expirations for AMC renewal campaigns and customer outreach
                  </p>
                </div>
              </div>
              <div style={{ width: '100%', height: '240px' }}>
                {summary?.expiry_timeline && summary.expiry_timeline.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={summary.expiry_timeline} margin={{ top: 10, right: 10, left: -20, bottom: 25 }}>
                      <XAxis dataKey="month" angle={-25} textAnchor="end" interval={0} tick={{ fontSize: 10, fill: '#4b5563' }} />
                      <YAxis tick={{ fontSize: 11, fill: '#4b5563' }} />
                      <Tooltip />
                      <Bar dataKey="expiring_count" fill="var(--color-amber-600)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#9ca3af', fontSize: '13px' }}>
                    No expirations in the upcoming 12 months
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Quick Shortcuts & SLA Assurance Banner */}
          <div
            className="aarka-card"
            style={{
              padding: '20px 24px',
              backgroundColor: '#effaf4',
              border: '1px solid #a7e4c2',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <div>
              <div style={{ fontSize: '14px', fontWeight: '700', color: '#0c2318' }}>
                AARKA Automated EPC Warranty Handover Protocol Active
              </div>
              <p style={{ fontSize: '12px', color: '#166534', margin: '4px 0 0 0' }}>
                Every completed solar installation automatically activates separate 10-yr panel product, 25-yr panel performance, 5-yr inverter, and 5-yr EPC workmanship warranties.
              </p>
            </div>
            <button onClick={() => setActiveTab('ALL_WARRANTIES')} className="btn btn-accent" style={{ fontSize: '12px' }}>
              Explore Warranties →
            </button>
          </div>
        </div>
      )}

      {/* TAB 2: ALL REGISTERED WARRANTIES */}
      {activeTab === 'ALL_WARRANTIES' && (
        <div>
          {/* Filters Bar */}
          <div className="aarka-card" style={{ padding: '16px', marginBottom: '16px', display: 'flex', gap: '12px', flexWrap: 'wrap', alignItems: 'center' }}>
            <div style={{ position: 'relative', flex: 1, minWidth: '240px' }}>
              <Search size={16} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#9ca3af' }} />
              <input
                type="text"
                placeholder="Search serial number, customer name, order number, or certificate..."
                value={searchFilter}
                onChange={(e) => setSearchFilter(e.target.value)}
                style={{
                  width: '100%',
                  padding: '8px 12px 8px 36px',
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--border-color)',
                  fontSize: '13px',
                  outline: 'none',
                }}
              />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Warranty Type:</span>
              <select
                value={typeFilter}
                onChange={(e) => setTypeFilter(e.target.value)}
                style={{ padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px' }}
              >
                <option value="ALL">All Warranty Types</option>
                <option value="PRODUCT">Product Warranty (Defects)</option>
                <option value="PERFORMANCE">Performance Warranty (Degradation)</option>
                <option value="WORKMANSHIP">Workmanship Warranty (AARKA EPC)</option>
              </select>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-muted)' }}>Status:</span>
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{ padding: '8px 12px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px' }}
              >
                <option value="ALL">All Statuses</option>
                <option value="ACTIVE">Active</option>
                <option value="EXPIRING_SOON">Expiring Soon (≤ 90d)</option>
                <option value="CLAIM_RAISED">Claim Raised</option>
                <option value="EXPIRED">Expired</option>
              </select>
            </div>

            {(searchFilter || typeFilter !== 'ALL' || statusFilter !== 'ALL') && (
              <button
                onClick={() => { setSearchFilter(''); setTypeFilter('ALL'); setStatusFilter('ALL'); }}
                className="btn btn-secondary"
                style={{ padding: '6px 12px', fontSize: '12px' }}
              >
                Reset Filters
              </button>
            )}
          </div>

          <DataTable
            title="Registered Equipment Warranty Master"
            subtitle={`Displaying ${filteredWarranties.length} activated warranty certificates`}
            columns={warrantyColumns}
            data={filteredWarranties}
            searchKey="serial_number"
            searchPlaceholder="Quick filter rows..."
          />
        </div>
      )}

      {/* TAB 3: EXPIRING SOON ALERTS */}
      {activeTab === 'EXPIRING' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '20px' }}>
            <div className="aarka-card" style={{ padding: '18px', borderLeft: '4px solid #dc2626' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#dc2626' }}>CRITICAL (≤ 7 DAYS)</span>
                <span style={{ fontSize: '20px', fontWeight: '800' }}>{alerts?.critical_7_days?.length || 0}</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '6px 0 0 0' }}>Urgent inspection or renewal needed</p>
            </div>

            <div className="aarka-card" style={{ padding: '18px', borderLeft: '4px solid #ea580c' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#ea580c' }}>URGENT (≤ 30 DAYS)</span>
                <span style={{ fontSize: '20px', fontWeight: '800' }}>{alerts?.urgent_30_days?.length || 0}</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '6px 0 0 0' }}>Notify customer for annual maintenance</p>
            </div>

            <div className="aarka-card" style={{ padding: '18px', borderLeft: '4px solid #d97706' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontWeight: '700', color: '#d97706' }}>ADVANCE NOTICE (≤ 90 DAYS)</span>
                <span style={{ fontSize: '20px', fontWeight: '800' }}>{alerts?.notice_90_days?.length || 0}</span>
              </div>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)', margin: '6px 0 0 0' }}>Schedule routine solar system health check</p>
            </div>
          </div>

          <div className="aarka-card" style={{ padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
              <h3 style={{ fontSize: '16px', fontWeight: '700', margin: 0 }}>Expiring Equipment Register</h3>
              <button onClick={handleTriggerAlerts} className="btn btn-accent" style={{ fontSize: '12px' }} disabled={actionLoading}>
                <Send size={14} style={{ marginRight: '6px' }} /> Dispatch Automated Customer SMS/Email Alerts
              </button>
            </div>

            {alerts && (alerts.critical_7_days.length > 0 || alerts.urgent_30_days.length > 0 || alerts.notice_90_days.length > 0) ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {[...alerts.critical_7_days, ...alerts.urgent_30_days, ...alerts.notice_90_days].map((item, idx) => (
                  <div
                    key={idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '12px 16px',
                      backgroundColor: 'var(--bg-page)',
                      borderRadius: 'var(--radius-md)',
                      border: '1px solid var(--border-color)',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: '700', fontSize: '13px' }}>
                        {item.serial_number} • {item.product_name}
                      </div>
                      <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                        Customer: {item.customer_name} ({item.customer_phone}) • Expiry: <strong>{item.warranty_end}</strong>
                      </div>
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <span style={{ fontSize: '12px', fontWeight: '700', color: item.days_remaining <= 7 ? '#dc2626' : '#d97706' }}>
                        {item.days_remaining} days remaining
                      </span>
                      <button
                        onClick={() => {
                          const w = warranties.find((w) => w.id === item.id);
                          if (w) setClaimModal({ open: true, warranty: w });
                        }}
                        className="btn btn-secondary"
                        style={{ fontSize: '11px', padding: '4px 8px' }}
                      >
                        Raise Claim
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ padding: '30px', textAlign: 'center', color: '#9ca3af', fontSize: '13px' }}>
                <CheckCircle size={28} color="#15803d" style={{ margin: '0 auto 8px auto', display: 'block' }} />
                No warranties are expiring within the next 90 days. All solar assets are healthy.
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: WARRANTY CLAIMS & RMA TRACKING */}
      {activeTab === 'CLAIMS' && (
        <div>
          <DataTable
            title="Warranty Claims & OEM RMA Register"
            subtitle="Manage manufacturer repair, defect claims, and replacement serial tracking"
            columns={claimColumns}
            data={claims}
            searchKey="claim_number"
            searchPlaceholder="Search claims by reference, serial, customer..."
          />
        </div>
      )}

      {/* TAB 5: INSTANT SERIAL VERIFICATION TOOL */}
      {activeTab === 'VERIFY' && (
        <div>
          <div className="aarka-card" style={{ maxWidth: '800px', margin: '0 auto', backgroundColor: '#0c2318', color: '#ffffff', padding: '32px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a7e4c2', fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', marginBottom: '8px' }}>
              <ShieldCheck size={18} /> Official Equipment Warranty Validation System
            </div>
            <h2 style={{ fontSize: '22px', fontWeight: '800', marginBottom: '8px', fontFamily: 'var(--font-display)' }}>
              Scan or Enter Equipment Serial Number
            </h2>
            <p style={{ fontSize: '13px', color: '#94bca7', marginBottom: '20px' }}>
              Instant verification for field technicians, service personnel, and customer support representatives.
            </p>

            <form onSubmit={handleQuickVerify} style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
              <div style={{ position: 'relative', flex: 1 }}>
                <Search size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#7ba08d' }} />
                <input
                  type="text"
                  placeholder="Enter Serial #, Warranty #, Customer Name, or Phone..."
                  value={quickQuery}
                  onChange={(e) => setQuickQuery(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '12px 14px 12px 42px',
                    backgroundColor: '#163827',
                    border: '1px solid #23533a',
                    borderRadius: 'var(--radius-md)',
                    color: '#ffffff',
                    fontSize: '14px',
                    outline: 'none',
                  }}
                />
              </div>
              <button type="submit" className="btn btn-accent" disabled={quickLoading}>
                {quickLoading ? 'Verifying...' : 'Validate Guarantee'}
              </button>
            </form>

            {quickResult && (
              <div style={{ backgroundColor: '#133524', padding: '20px', borderRadius: '8px', border: '1px solid #23533a' }}>
                {quickResult.results.length === 0 ? (
                  <div style={{ color: '#fca5a5', fontSize: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <AlertCircle size={18} /> No active warranty found for '{quickQuery}'. Please ensure the installation was marked completed.
                  </div>
                ) : (
                  <div>
                    <div style={{ fontSize: '13px', color: '#a7e4c2', fontWeight: '700', marginBottom: '12px' }}>
                      Verified {quickResult.results.length} Active Warranty Record(s):
                    </div>
                    {quickResult.results.map((r, idx) => (
                      <div
                        key={idx}
                        style={{
                          backgroundColor: '#0c2318',
                          padding: '14px 16px',
                          borderRadius: '8px',
                          marginBottom: '10px',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                        }}
                      >
                        <div>
                          <div style={{ fontWeight: '700', fontSize: '15px', color: '#ffffff' }}>
                            {r.serial_number} • {r.product_name}
                          </div>
                          <div style={{ fontSize: '12px', color: '#a7e4c2', marginTop: '4px' }}>
                            Type: <strong>{r.warranty_type}</strong> • Beneficiary: {r.customer_name} ({r.customer_phone})
                          </div>
                          <div style={{ fontSize: '11px', color: '#94bca7', marginTop: '2px' }}>
                            Valid From: {r.warranty_start} until {r.warranty_end}
                          </div>
                        </div>
                        <div style={{ textAlign: 'right' }}>
                          <StatusBadge status={r.status} />
                          <div style={{ fontSize: '12px', color: '#34d399', fontWeight: '700', marginTop: '4px' }}>
                            {r.days_remaining} Days Remaining
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* MODAL 1: OFFICIAL WARRANTY CERTIFICATE */}
      {certificateModal.open && (
        <Modal
          isOpen={certificateModal.open}
          onClose={() => setCertificateModal({ open: false, data: null, loading: false })}
          title="Digital Warranty Certificate"
        >
          {certificateModal.loading ? (
            <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
              <RefreshCw className="animate-spin" size={24} style={{ margin: '0 auto 8px auto' }} />
              Generating digital certificate...
            </div>
          ) : certificateModal.data ? (
            <div>
              {/* Printable Certificate Box */}
              <div
                id="printable-warranty-certificate"
                style={{
                  padding: '28px',
                  border: '2px solid #0c2318',
                  borderRadius: 'var(--radius-lg)',
                  backgroundColor: '#ffffff',
                  color: '#0c2318',
                  position: 'relative',
                }}
              >
                {/* Header with Brand */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '2px solid #0c2318', paddingBottom: '16px', marginBottom: '20px' }}>
                  <div>
                    <h2 style={{ margin: 0, fontSize: '20px', fontWeight: '800', color: '#0c2318', fontFamily: 'var(--font-display)' }}>
                      AARKA SOLAR OPERATIONS
                    </h2>
                    <span style={{ fontSize: '11px', letterSpacing: '0.1em', textTransform: 'uppercase', color: '#047857', fontWeight: '700' }}>
                      Official Equipment Warranty & Performance Certificate
                    </span>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '12px', fontWeight: '700', fontFamily: 'monospace' }}>
                      {certificateModal.data.certificate_number}
                    </div>
                    <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                      Issue Date: {certificateModal.data.issue_date}
                    </div>
                  </div>
                </div>

                {/* Beneficiary & Site Info */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px', backgroundColor: '#f7f8f5', padding: '14px', borderRadius: '8px' }}>
                  <div>
                    <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#6b7280', fontWeight: '700' }}>Registered Beneficiary</div>
                    <div style={{ fontWeight: '700', fontSize: '14px' }}>{certificateModal.data.beneficiary.customer_name}</div>
                    <div style={{ fontSize: '12px', color: '#4b5563' }}>{certificateModal.data.beneficiary.address}</div>
                    <div style={{ fontSize: '12px', color: '#4b5563' }}>Phone: {certificateModal.data.beneficiary.phone}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', textTransform: 'uppercase', color: '#6b7280', fontWeight: '700' }}>System Installation Reference</div>
                    <div style={{ fontWeight: '700', fontSize: '14px' }}>Order #{certificateModal.data.beneficiary.order_number}</div>
                    <div style={{ fontSize: '12px', color: '#4b5563' }}>Installed Capacity: {certificateModal.data.beneficiary.capacity_kw} kW Grid-Tied Solar</div>
                    <div style={{ fontSize: '12px', color: '#047857', fontWeight: '600' }}>Status: {certificateModal.data.status}</div>
                  </div>
                </div>

                {/* Equipment Specifications */}
                <div style={{ marginBottom: '20px' }}>
                  <div style={{ fontSize: '12px', fontWeight: '700', textTransform: 'uppercase', color: '#0c2318', marginBottom: '8px' }}>
                    Guaranteed Equipment Details
                  </div>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '12px' }}>
                    <tbody>
                      <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '6px 0', color: '#6b7280', width: '35%' }}>Equipment Name:</td>
                        <td style={{ padding: '6px 0', fontWeight: '600' }}>{certificateModal.data.equipment.product_name}</td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '6px 0', color: '#6b7280' }}>Serial Number:</td>
                        <td style={{ padding: '6px 0', fontWeight: '700', fontFamily: 'monospace', color: '#b45309' }}>
                          {certificateModal.data.equipment.serial_number}
                        </td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '6px 0', color: '#6b7280' }}>Manufacturer & Model:</td>
                        <td style={{ padding: '6px 0' }}>{certificateModal.data.equipment.manufacturer} ({certificateModal.data.equipment.model})</td>
                      </tr>
                      <tr style={{ borderBottom: '1px solid #e5e7eb' }}>
                        <td style={{ padding: '6px 0', color: '#6b7280' }}>Warranty Type & Tenure:</td>
                        <td style={{ padding: '6px 0', fontWeight: '700', color: '#047857' }}>
                          {certificateModal.data.warranty_type} ({certificateModal.data.duration_years} Years)
                        </td>
                      </tr>
                      <tr>
                        <td style={{ padding: '6px 0', color: '#6b7280' }}>Validity Expiry Date:</td>
                        <td style={{ padding: '6px 0', fontWeight: '700' }}>{certificateModal.data.expiry_date}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>

                {/* Coverage Terms & SLA */}
                <div style={{ fontSize: '11px', color: '#4b5563', borderTop: '1px solid #e5e7eb', paddingTop: '14px', marginBottom: '20px' }}>
                  <div style={{ fontWeight: '700', color: '#0c2318', marginBottom: '4px' }}>Terms & SLA:</div>
                  <p style={{ margin: '0 0 4px 0' }}>{certificateModal.data.terms.summary}</p>
                  <p style={{ margin: '0 0 4px 0' }}><em>Exclusions:</em> {certificateModal.data.terms.exclusions}</p>
                  <p style={{ margin: 0 }}><strong>SLA:</strong> {certificateModal.data.terms.service_sla}</p>
                </div>

                {/* Sign-off Seal */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', borderTop: '2px solid #0c2318', paddingTop: '16px' }}>
                  <div style={{ fontSize: '11px', color: '#6b7280' }}>
                    Helpline: {certificateModal.data.issuer.support_helpline} • {certificateModal.data.issuer.portal}
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontWeight: '700', fontSize: '12px' }}>AARKA Quality & Engineering Team</div>
                    <div style={{ fontSize: '11px', color: '#047857' }}>Certified Solar Operations</div>
                  </div>
                </div>
              </div>

              {/* Print Action */}
              <div style={{ marginTop: '16px', display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  onClick={() => window.print()}
                  className="btn btn-accent"
                  style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                >
                  <Printer size={16} /> Print Official Certificate
                </button>
              </div>
            </div>
          ) : null}
        </Modal>
      )}

      {/* MODAL 2: RAISE WARRANTY CLAIM */}
      {claimModal.open && (
        <Modal
          isOpen={claimModal.open}
          onClose={() => setClaimModal({ open: false, warranty: null })}
          title="Lodge Equipment Warranty Claim (RMA)"
        >
          {claimModal.warranty && (
            <form onSubmit={handleSubmitClaim}>
              <div style={{ backgroundColor: '#f7f8f5', padding: '12px 14px', borderRadius: '8px', marginBottom: '16px', fontSize: '13px' }}>
                <div>Guaranteed Equipment: <strong>{claimModal.warranty.product_name}</strong></div>
                <div>Serial Number: <strong style={{ color: '#b45309', fontFamily: 'monospace' }}>{claimModal.warranty.serial_number}</strong></div>
                <div>Customer: <strong>{claimModal.warranty.customer_name}</strong> ({claimModal.warranty.customer_phone})</div>
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px' }}>
                  Issue Description & Fault Symptoms *
                </label>
                <textarea
                  rows={4}
                  required
                  placeholder="Describe the failure, error codes (e.g. Inverter Error E04, DC under-voltage), or physical defect observed..."
                  value={claimForm.issue_description}
                  onChange={(e) => setClaimForm({ ...claimForm, issue_description: e.target.value })}
                  style={{ width: '100%', padding: '10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px' }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px' }}>
                    OEM Manufacturer RMA / Tracking Ref
                  </label>
                  <input
                    type="text"
                    placeholder="e.g. SUNGROW-RMA-8849"
                    value={claimForm.manufacturer_reference}
                    onChange={(e) => setClaimForm({ ...claimForm, manufacturer_reference: e.target.value })}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px' }}>
                    Assign Field Technician
                  </label>
                  <select
                    value={claimForm.assigned_technician_id}
                    onChange={(e) => setClaimForm({ ...claimForm, assigned_technician_id: e.target.value })}
                    style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px' }}
                  >
                    <option value="">Select Technician...</option>
                    {technicians.map((t) => (
                      <option key={t.id} value={t.id}>{t.name} ({t.skill_level || 'Field Tech'})</option>
                    ))}
                  </select>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
                <button
                  type="button"
                  onClick={() => setClaimModal({ open: false, warranty: null })}
                  className="btn btn-secondary"
                  disabled={actionLoading}
                >
                  Cancel
                </button>
                <button type="submit" className="btn btn-accent" disabled={actionLoading}>
                  {actionLoading ? 'Submitting...' : 'Submit Claim'}
                </button>
              </div>
            </form>
          )}
        </Modal>
      )}

      {/* MODAL 3: UPDATE CLAIM STATUS */}
      {claimStatusModal.open && (
        <Modal
          isOpen={claimStatusModal.open}
          onClose={() => setClaimStatusModal({ open: false, claim: null })}
          title={`Update Claim #${claimStatusModal.claim?.claim_number}`}
        >
          <form onSubmit={handleUpdateClaimStatus}>
            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px' }}>
                Claim Lifecycle Stage *
              </label>
              <select
                value={claimStatusForm.claim_status}
                onChange={(e) => setClaimStatusForm({ ...claimStatusForm, claim_status: e.target.value })}
                style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px' }}
              >
                <option value="CLAIM_RAISED">Claim Raised</option>
                <option value="UNDER_REVIEW">Under Review with OEM</option>
                <option value="APPROVED_BY_OEM">Approved by OEM</option>
                <option value="REPLACEMENT_IN_PROGRESS">Replacement/Repair in Progress</option>
                <option value="REPAIRED">Repaired</option>
                <option value="RESOLVED">Resolved (Customer Handover Completed)</option>
                <option value="REJECTED">Rejected</option>
              </select>
            </div>

            <div style={{ marginBottom: '14px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px' }}>
                Manufacturer RMA Reference
              </label>
              <input
                type="text"
                value={claimStatusForm.manufacturer_reference}
                onChange={(e) => setClaimStatusForm({ ...claimStatusForm, manufacturer_reference: e.target.value })}
                style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px' }}
              />
            </div>

            {['REPLACEMENT_IN_PROGRESS', 'RESOLVED'].includes(claimStatusForm.claim_status) && (
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px' }}>
                  Replacement Equipment Serial Number
                </label>
                <input
                  type="text"
                  placeholder="Enter new unit serial number..."
                  value={claimStatusForm.replacement_serial_number}
                  onChange={(e) => setClaimStatusForm({ ...claimStatusForm, replacement_serial_number: e.target.value })}
                  style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px', fontFamily: 'monospace' }}
                />
              </div>
            )}

            <div style={{ marginBottom: '16px' }}>
              <label style={{ display: 'block', fontSize: '12px', fontWeight: '700', marginBottom: '4px' }}>
                Resolution / Engineering Notes
              </label>
              <textarea
                rows={3}
                placeholder="Details of OEM RMA outcome, parts replaced, or customer acceptance..."
                value={claimStatusForm.resolution_details}
                onChange={(e) => setClaimStatusForm({ ...claimStatusForm, resolution_details: e.target.value })}
                style={{ width: '100%', padding: '8px 10px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border-color)', fontSize: '13px' }}
              />
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '8px' }}>
              <button
                type="button"
                onClick={() => setClaimStatusModal({ open: false, claim: null })}
                className="btn btn-secondary"
                disabled={actionLoading}
              >
                Cancel
              </button>
              <button type="submit" className="btn btn-accent" disabled={actionLoading}>
                {actionLoading ? 'Saving...' : 'Save Lifecycle Status'}
              </button>
            </div>
          </form>
        </Modal>
      )}
    </div>
  );
};

export default WarrantiesPage;
