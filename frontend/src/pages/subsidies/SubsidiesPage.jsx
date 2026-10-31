import React, { useState, useEffect } from 'react';
import { 
  Building, Plus, Search, CheckCircle, Clock, AlertTriangle, 
  FileCheck, Shield, ChevronRight, Landmark 
} from 'lucide-react';
import { subsidiesApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';
import StatusBadge from '../../components/common/StatusBadge';
import DataTable from '../../components/common/DataTable';
import Modal from '../../components/common/Modal';

export default function SubsidiesPage() {
  const [subsidies, setSubsidies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showApplyModal, setShowApplyModal] = useState(false);
  const [showStatusModal, setShowStatusModal] = useState(false);
  const [selectedSubsidy, setSelectedSubsidy] = useState(null);

  const [applyForm, setApplyForm] = useState({
    order_id: '',
    application_reference: '',
    discom_name: 'TSSPDCL',
    consumer_number: '',
    subsidy_scheme: 'PM_SURYA_GHAR_MUFT_BIJLI_YOJANA',
    eligible_amount: 78000
  });

  const [statusForm, setStatusForm] = useState({
    status: 'DOCS_VERIFIED',
    notes: '',
    inspection_date: '',
    sanctioned_amount: 78000,
    disbursement_reference: ''
  });

  const [feedback, setFeedback] = useState(null);

  const fetchSubsidies = async () => {
    try {
      setLoading(true);
      const res = await subsidiesApi.getAll();
      setSubsidies(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSubsidies();
  }, []);

  const handleApply = async (e) => {
    e.preventDefault();
    try {
      await subsidiesApi.create({
        ...applyForm,
        order_id: parseInt(applyForm.order_id),
        eligible_amount: parseFloat(applyForm.eligible_amount)
      });
      setFeedback({ type: 'success', msg: 'Subsidy application registered successfully!' });
      setShowApplyModal(false);
      setApplyForm({
        order_id: '',
        application_reference: '',
        discom_name: 'TSSPDCL',
        consumer_number: '',
        subsidy_scheme: 'PM_SURYA_GHAR_MUFT_BIJLI_YOJANA',
        eligible_amount: 78000
      });
      fetchSubsidies();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Failed to apply' });
    }
  };

  const handleUpdateStatus = async (e) => {
    e.preventDefault();
    try {
      await subsidiesApi.updateStatus(selectedSubsidy.id, {
        status: statusForm.status,
        notes: statusForm.notes,
        inspection_date: statusForm.inspection_date || null,
        sanctioned_amount: statusForm.sanctioned_amount ? parseFloat(statusForm.sanctioned_amount) : null,
        disbursement_reference: statusForm.disbursement_reference || null
      });
      setFeedback({ type: 'success', msg: `Application updated to ${statusForm.status}` });
      setShowStatusModal(false);
      fetchSubsidies();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Update failed' });
    }
  };

  const openStatusModal = (sub) => {
    setSelectedSubsidy(sub);
    setStatusForm({
      status: sub.status === 'DRAFT' ? 'SUBMITTED' : sub.status,
      notes: sub.discom_remarks || '',
      inspection_date: sub.inspection_scheduled_date || '',
      sanctioned_amount: sub.sanctioned_amount || sub.eligible_amount,
      disbursement_reference: sub.disbursement_reference || ''
    });
    setShowStatusModal(true);
  };

  const filtered = subsidies.filter(s =>
    s.application_reference?.toLowerCase().includes(search.toLowerCase()) ||
    s.consumer_number?.toLowerCase().includes(search.toLowerCase()) ||
    s.discom_name?.toLowerCase().includes(search.toLowerCase())
  );

  const columns = [
    {
      header: 'App Ref #',
      accessor: 'application_reference',
      cell: (row) => (
        <span className="font-mono font-semibold text-emerald-800 text-sm">
          {row.application_reference || `SUB-${row.id}`}
        </span>
      )
    },
    {
      header: 'Order / Customer',
      accessor: 'order_id',
      cell: (row) => (
        <div>
          <div className="font-medium text-stone-900">Sales Order #{row.order_id}</div>
          <div className="text-xs text-stone-500 font-mono">Cons. No: {row.consumer_number}</div>
        </div>
      )
    },
    {
      header: 'DISCOM & Scheme',
      accessor: 'discom_name',
      cell: (row) => (
        <div>
          <div className="text-xs font-semibold text-stone-800">{row.discom_name}</div>
          <div className="text-[11px] text-stone-500">
            {row.subsidy_scheme === 'PM_SURYA_GHAR_MUFT_BIJLI_YOJANA' ? 'PM Surya Ghar (National Portal)' : row.subsidy_scheme}
          </div>
        </div>
      )
    },
    {
      header: 'Eligible Subsidy',
      accessor: 'eligible_amount',
      cell: (row) => (
        <span className="font-bold text-stone-900">
          ₹{row.eligible_amount?.toLocaleString('en-IN')}
        </span>
      )
    },
    {
      header: 'Disbursed Amount',
      accessor: 'disbursed_amount',
      cell: (row) => (
        <span className={`font-semibold ${row.disbursed_amount > 0 ? 'text-emerald-700' : 'text-stone-400'}`}>
          {row.disbursed_amount > 0 ? `₹${row.disbursed_amount.toLocaleString('en-IN')}` : '₹0 (Pending)'}
        </span>
      )
    },
    {
      header: 'Status',
      accessor: 'status',
      cell: (row) => <StatusBadge status={row.status} />
    },
    {
      header: 'Actions',
      cell: (row) => (
        <button
          onClick={() => openStatusModal(row)}
          className="text-xs px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-800 rounded font-medium transition-colors"
        >
          Update Stage
        </button>
      )
    }
  ];

  const totalEligible = subsidies.reduce((s, c) => s + (c.eligible_amount || 0), 0);
  const totalDisbursed = subsidies.reduce((s, c) => s + (c.disbursed_amount || 0), 0);
  const pendingApprovals = subsidies.filter(s => ['SUBMITTED', 'DOCS_VERIFIED', 'INSPECTION_SCHEDULED'].includes(s.status)).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Government Subsidies & DISCOM Liaison</h1>
          <p className="text-sm text-stone-600 mt-1">
            Track PM Surya Ghar Muft Bijli Yojana subsidy lifecycle, DISCOM inspections, and DBT direct disbursements.
          </p>
        </div>
        <button
          onClick={() => setShowApplyModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          New Application
        </button>
      </div>

      {feedback && (
        <div className={`p-4 rounded-lg flex items-center justify-between text-sm ${
          feedback.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-rose-50 text-rose-800 border border-rose-200'
        }`}>
          <span>{feedback.msg}</span>
          <button onClick={() => setFeedback(null)} className="text-xs underline font-medium">Dismiss</button>
        </div>
      )}

      {/* KPI Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Applications" value={subsidies.length} icon={Landmark} subtitle="Registered subsidy files" />
        <StatCard title="Pending Inspections" value={pendingApprovals} icon={Clock} subtitle="DISCOM site clearance" />
        <StatCard title="Total Eligible Claim" value={`₹${totalEligible.toLocaleString('en-IN')}`} icon={FileCheck} subtitle="Approved pool under PM Surya Ghar" />
        <StatCard title="Disbursed DBT" value={`₹${totalDisbursed.toLocaleString('en-IN')}`} icon={CheckCircle} subtitle="Credited to customer accounts" />
      </div>

      {/* Search */}
      <div className="bg-white p-4 rounded-xl border border-stone-200 flex items-center justify-between shadow-sm">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search ref #, consumer #, DISCOM..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>
      </div>

      <DataTable
        columns={columns}
        data={filtered}
        loading={loading}
        emptyMessage="No subsidy applications found."
      />

      {/* New Application Modal */}
      <Modal
        isOpen={showApplyModal}
        onClose={() => setShowApplyModal(false)}
        title="File New PM Surya Ghar Subsidy Application"
      >
        <form onSubmit={handleApply} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Sales Order ID *</label>
            <input
              type="number"
              required
              placeholder="e.g. 1"
              value={applyForm.order_id}
              onChange={(e) => setApplyForm({ ...applyForm, order_id: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">National Portal Application Ref</label>
              <input
                type="text"
                required
                placeholder="e.g. PMSGY-2026-98124"
                value={applyForm.application_reference}
                onChange={(e) => setApplyForm({ ...applyForm, application_reference: e.target.value })}
                className="w-full px-3 py-2 text-sm font-mono border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">DISCOM Consumer / USC Number</label>
              <input
                type="text"
                required
                placeholder="e.g. 1029384756"
                value={applyForm.consumer_number}
                onChange={(e) => setApplyForm({ ...applyForm, consumer_number: e.target.value })}
                className="w-full px-3 py-2 text-sm font-mono border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">DISCOM Name</label>
              <input
                type="text"
                required
                placeholder="e.g. TSSPDCL / BESCOM / TANGEDCO"
                value={applyForm.discom_name}
                onChange={(e) => setApplyForm({ ...applyForm, discom_name: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Eligible Subsidy Claim (₹)</label>
              <input
                type="number"
                required
                placeholder="78000"
                value={applyForm.eligible_amount}
                onChange={(e) => setApplyForm({ ...applyForm, eligible_amount: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowApplyModal(false)}
              className="px-4 py-2 border border-stone-300 text-stone-700 rounded-lg text-sm hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-sm font-medium hover:bg-emerald-900"
            >
              Create Subsidy File
            </button>
          </div>
        </form>
      </Modal>

      {/* Update Status Modal */}
      <Modal
        isOpen={showStatusModal}
        onClose={() => setShowStatusModal(false)}
        title={`Update Subsidy Lifecycle — ${selectedSubsidy?.application_reference}`}
      >
        <form onSubmit={handleUpdateStatus} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Application Lifecycle Stage</label>
            <select
              value={statusForm.status}
              onChange={(e) => setStatusForm({ ...statusForm, status: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none bg-white"
            >
              <option value="DRAFT">Draft</option>
              <option value="SUBMITTED">Submitted to Portal</option>
              <option value="DOCS_VERIFIED">Documents Verified by DISCOM</option>
              <option value="INSPECTION_SCHEDULED">DISCOM Field Inspection Scheduled</option>
              <option value="INSPECTION_PASSED">Net Meter Installed & Inspection Passed</option>
              <option value="APPROVED">Subsidy Sanctioned</option>
              <option value="DISBURSED">DBT Disbursed to Bank Account</option>
              <option value="REJECTED">Application Rejected</option>
            </select>
          </div>

          {['INSPECTION_SCHEDULED', 'INSPECTION_PASSED'].includes(statusForm.status) && (
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">DISCOM Inspection Date</label>
              <input
                type="date"
                value={statusForm.inspection_date}
                onChange={(e) => setStatusForm({ ...statusForm, inspection_date: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          )}

          {['APPROVED', 'DISBURSED'].includes(statusForm.status) && (
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Sanctioned / Disbursed Amount (₹)</label>
                <input
                  type="number"
                  value={statusForm.sanctioned_amount}
                  onChange={(e) => setStatusForm({ ...statusForm, sanctioned_amount: e.target.value })}
                  className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">DBT Reference / UTR #</label>
                <input
                  type="text"
                  placeholder="e.g. UTR-20261031-987"
                  value={statusForm.disbursement_reference}
                  onChange={(e) => setStatusForm({ ...statusForm, disbursement_reference: e.target.value })}
                  className="w-full px-3 py-2 text-sm font-mono border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
                />
              </div>
            </div>
          )}

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Notes / Official Remarks</label>
            <textarea
              rows={3}
              placeholder="e.g. Net meter bi-directional synchronization tested by DISCOM AE..."
              value={statusForm.notes}
              onChange={(e) => setStatusForm({ ...statusForm, notes: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowStatusModal(false)}
              className="px-4 py-2 border border-stone-300 text-stone-700 rounded-lg text-sm hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-sm font-medium hover:bg-emerald-900"
            >
              Save Lifecycle Stage
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
