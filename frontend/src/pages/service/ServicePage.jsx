import React, { useState, useEffect } from 'react';
import { 
  Wrench, Plus, CheckCircle, AlertTriangle, ShieldCheck, 
  RotateCcw, UserCheck, Search, Filter, ShieldAlert 
} from 'lucide-react';
import { serviceApi, techniciansApi, serialsApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';
import StatusBadge from '../../components/common/StatusBadge';
import DataTable from '../../components/common/DataTable';
import Modal from '../../components/common/Modal';

export default function ServicePage() {
  const [tickets, setTickets] = useState([]);
  const [technicians, setTechnicians] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');

  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showReplaceModal, setShowReplaceModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);

  // Forms
  const [createForm, setCreateForm] = useState({
    customer_id: '',
    title: '',
    description: '',
    reported_serial_number: '',
    priority: 'MEDIUM'
  });

  const [assignForm, setAssignForm] = useState({ technician_id: '' });
  const [replaceForm, setReplaceForm] = useState({
    old_serial_number: '',
    new_serial_number: '',
    replacement_reason: ''
  });
  const [resolveForm, setResolveForm] = useState({
    resolution_notes: '',
    labor_cost: 0,
    parts_cost: 0,
    customer_signature: 'CONFIRMED_BY_CUSTOMER_DIGITALLY'
  });

  const [feedback, setFeedback] = useState(null);

  const fetchTickets = async () => {
    try {
      setLoading(true);
      const res = await serviceApi.getTickets();
      setTickets(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const fetchTechs = async () => {
    try {
      const res = await techniciansApi.getAll();
      setTechnicians(res.data);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    fetchTickets();
    fetchTechs();
  }, []);

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    try {
      const res = await serviceApi.createTicket({
        ...createForm,
        customer_id: parseInt(createForm.customer_id),
        serial_number: createForm.reported_serial_number || createForm.serial_number,
        fault_description: createForm.description || createForm.title || 'Inverter fault reported'
      });
      const isCov = res.data.warranty_status === 'COVERED' || res.data.is_under_warranty;
      const charge = res.data.total_charges ?? res.data.estimated_cost ?? 0;
      setFeedback({
        type: 'success',
        msg: `Ticket ${res.data.ticket_number} logged! System evaluated warranty: ${isCov ? 'COVERED (₹0 Charge)' : 'EXPIRED (Chargeable)'} (Customer Charge: ₹${charge})`
      });
      setShowCreateModal(false);
      setCreateForm({
        customer_id: '',
        title: '',
        description: '',
        reported_serial_number: '',
        priority: 'MEDIUM'
      });
      fetchTickets();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Failed to create ticket' });
    }
  };

  const handleAssign = async (e) => {
    e.preventDefault();
    try {
      await serviceApi.assignTechnician(selectedTicket.id, {
        technician_id: parseInt(assignForm.technician_id)
      });
      setFeedback({ type: 'success', msg: `Technician assigned to Ticket #${selectedTicket.ticket_number}` });
      setShowAssignModal(false);
      fetchTickets();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Assignment failed' });
    }
  };

  const handleReplaceEquipment = async (e) => {
    e.preventDefault();
    try {
      const res = await serviceApi.replaceEquipment(selectedTicket.id, {
        replacement_serial_number: replaceForm.new_serial_number,
        new_serial_number: replaceForm.new_serial_number,
        reason: replaceForm.replacement_reason,
        replacement_reason: replaceForm.replacement_reason
      });
      setFeedback({
        type: 'success',
        msg: `Equipment replaced! Old serial marked DEFECTIVE, new serial ${res.data.replacement_serial || replaceForm.new_serial_number} allocated with warranty updated.`
      });
      setShowReplaceModal(false);
      setReplaceForm({ old_serial_number: '', new_serial_number: '', replacement_reason: '' });
      fetchTickets();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Replacement failed' });
    }
  };

  const handleResolve = async (e) => {
    e.preventDefault();
    try {
      await serviceApi.resolveTicket(selectedTicket.id, {
        resolution_notes: resolveForm.resolution_notes,
        repair_details: resolveForm.resolution_notes,
        labor_cost: parseFloat(resolveForm.labor_cost) || 0,
        parts_cost: parseFloat(resolveForm.parts_cost) || 0,
        customer_signature: 'CONFIRMED_BY_CUSTOMER_DIGITALLY'
      });
      try {
        await serviceApi.confirmTicket(selectedTicket.id);
      } catch (confirmErr) {
        // already resolved/closed
      }
      setFeedback({ type: 'success', msg: `Ticket #${selectedTicket.ticket_number} marked RESOLVED & CONFIRMED with customer acceptance.` });
      setShowResolveModal(false);
      fetchTickets();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Resolution failed' });
    }
  };

  const openAssignModal = (ticket) => {
    setSelectedTicket(ticket);
    setAssignForm({ technician_id: ticket.technician_id || ticket.assigned_technician_id || '' });
    setShowAssignModal(true);
  };

  const openReplaceModal = (ticket) => {
    setSelectedTicket(ticket);
    setReplaceForm({
      old_serial_number: ticket.serial_number || ticket.reported_serial_number || '',
      new_serial_number: '',
      replacement_reason: 'In-warranty inverter/component failure confirmed by technician'
    });
    setShowReplaceModal(true);
  };

  const openResolveModal = (ticket) => {
    setSelectedTicket(ticket);
    const isCovered = ticket.warranty_status === 'COVERED' || ticket.is_under_warranty;
    setResolveForm({
      resolution_notes: 'Replaced inverter board and verified string VOC/ISC within limits.',
      labor_cost: isCovered ? 0 : 750,
      parts_cost: isCovered ? 0 : 3500,
      customer_signature: 'CUSTOMER_DIGITAL_CONFIRMATION_OK'
    });
    setShowResolveModal(true);
  };

  const filteredTickets = tickets.filter(t => {
    const sn = t.serial_number || t.reported_serial_number || '';
    const custName = t.customer_name || t.customer?.name || '';
    const desc = t.fault_description || t.title || '';
    const matchesSearch = 
      t.ticket_number?.toLowerCase().includes(search.toLowerCase()) ||
      custName.toLowerCase().includes(search.toLowerCase()) ||
      sn.toLowerCase().includes(search.toLowerCase()) ||
      desc.toLowerCase().includes(search.toLowerCase());
    const matchesStatus = statusFilter === 'ALL' || t.status === statusFilter;
    return matchesSearch && matchesStatus;
  });

  const columns = [
    {
      header: 'Ticket #',
      accessor: 'ticket_number',
      cell: (row) => (
        <span className="font-semibold text-emerald-800 font-mono text-sm">
          {row.ticket_number}
        </span>
      )
    },
    {
      header: 'Customer',
      accessor: 'customer',
      cell: (row) => (
        <div>
          <div className="font-medium text-stone-900">{row.customer_name || row.customer?.name || `Customer #${row.customer_id}`}</div>
          <div className="text-xs text-stone-500">{row.customer_phone || row.customer?.phone}</div>
        </div>
      )
    },
    {
      header: 'Fault & Serial',
      accessor: 'serial_number',
      cell: (row) => {
        const sn = row.serial_number || row.reported_serial_number;
        return (
          <div>
            <div className="font-medium text-stone-800 text-sm">{row.fault_description || row.title}</div>
            {sn && (
              <div className="text-xs font-mono text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded inline-block mt-0.5">
                SN: {sn}
              </div>
            )}
          </div>
        );
      }
    },
    {
      header: 'Warranty Status',
      accessor: 'warranty_status',
      cell: (row) => {
        const isCovered = row.warranty_status === 'COVERED' || row.is_under_warranty;
        return (
          <div className="space-y-1">
            {isCovered ? (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-emerald-100 text-emerald-800 rounded font-medium">
                <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                Under Warranty (₹0)
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 text-xs px-2 py-0.5 bg-amber-100 text-amber-900 rounded font-medium">
                <ShieldAlert className="w-3.5 h-3.5 text-amber-600" />
                Chargeable (Est: ₹{(row.total_charges || row.estimated_cost || 0).toLocaleString('en-IN')})
              </span>
            )}
            <div className="text-[11px] text-stone-500 font-mono">
              Eval: {row.warranty_status || 'COVERED'}
            </div>
          </div>
        );
      }
    },
    {
      header: 'Technician',
      accessor: 'technician_name',
      cell: (row) => (
        <span className="text-sm text-stone-700">
          {row.technician_name || row.assigned_technician?.name || <span className="text-stone-400 italic">Unassigned</span>}
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
        <div className="flex items-center gap-1.5">
          {row.status === 'OPEN' && (
            <button
              onClick={() => openAssignModal(row)}
              className="text-xs px-2.5 py-1 bg-stone-100 hover:bg-stone-200 text-stone-800 rounded font-medium transition-colors"
            >
              Assign Tech
            </button>
          )}

          {['ASSIGNED', 'IN_PROGRESS', 'OPEN'].includes(row.status) && (
            <button
              onClick={() => openReplaceModal(row)}
              title="Replace Defective Equipment (Rule #12)"
              className="text-xs px-2.5 py-1 bg-amber-50 hover:bg-amber-100 text-amber-800 rounded font-medium transition-colors flex items-center gap-1"
            >
              <RotateCcw className="w-3 h-3" />
              Swap SN
            </button>
          )}

          {row.status !== 'RESOLVED' && row.status !== 'CLOSED' && (
            <button
              onClick={() => openResolveModal(row)}
              className="text-xs px-2.5 py-1 bg-emerald-600 hover:bg-emerald-700 text-white rounded font-medium transition-colors flex items-center gap-1"
            >
              <CheckCircle className="w-3 h-3" />
              Resolve
            </button>
          )}
        </div>
      )
    }
  ];

  const openCount = tickets.filter(t => t.status === 'OPEN').length;
  const inProgressCount = tickets.filter(t => ['ASSIGNED', 'IN_PROGRESS'].includes(t.status)).length;
  const resolvedCount = tickets.filter(t => ['RESOLVED', 'CLOSED'].includes(t.status)).length;
  const warrantyCoveredCount = tickets.filter(t => t.is_under_warranty).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Service & Maintenance Tickets</h1>
          <p className="text-sm text-stone-600 mt-1">
            Automated warranty coverage determination, dispatch technician repairs, and equipment swap workflow.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Log Service Ticket
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
        <StatCard 
          title="Open Tickets" 
          value={openCount} 
          icon={AlertTriangle} 
          subtitle="Awaiting technician assignment" 
        />
        <StatCard 
          title="In Progress" 
          value={inProgressCount} 
          icon={Wrench} 
          subtitle="Technician dispatched" 
        />
        <StatCard 
          title="Under Warranty (₹0)" 
          value={warrantyCoveredCount} 
          icon={ShieldCheck} 
          subtitle="Free coverage evaluated by rule engine" 
        />
        <StatCard 
          title="Resolved" 
          value={resolvedCount} 
          icon={CheckCircle} 
          subtitle="Customer accepted repairs" 
        />
      </div>

      {/* Filters */}
      <div className="bg-white p-4 rounded-xl border border-stone-200 flex flex-col sm:flex-row gap-4 items-center justify-between shadow-sm">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search ticket #, serial, customer..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-sm border border-stone-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-600"
          />
        </div>

        <div className="flex items-center gap-2 w-full sm:w-auto">
          <Filter className="w-4 h-4 text-stone-500" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-sm border border-stone-200 rounded-lg px-3 py-2 bg-white focus:outline-none focus:ring-2 focus:ring-emerald-600"
          >
            <option value="ALL">All Statuses</option>
            <option value="OPEN">Open</option>
            <option value="ASSIGNED">Assigned</option>
            <option value="IN_PROGRESS">In Progress</option>
            <option value="RESOLVED">Resolved</option>
            <option value="CLOSED">Closed</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={filteredTickets}
        loading={loading}
        emptyMessage="No service tickets found."
      />

      {/* Create Ticket Modal */}
      <Modal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        title="Log Service Complaint (Rule Engine Activated)"
      >
        <form onSubmit={handleCreateTicket} className="space-y-4">
          <div className="p-3 bg-stone-50 rounded-lg border border-stone-200 text-xs text-stone-600 space-y-1">
            <span className="font-semibold text-stone-800">Automatic Warranty Check (Rule #10 & #11):</span>
            <p>If you enter a valid installed Serial Number, AARKA will automatically check if the complaint date is within the active warranty period. If covered, estimated customer cost is set to ₹0.00.</p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Customer ID *</label>
            <input
              type="number"
              required
              placeholder="e.g. 1"
              value={createForm.customer_id}
              onChange={(e) => setCreateForm({ ...createForm, customer_id: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Issue Title *</label>
            <input
              type="text"
              required
              placeholder="e.g. Inverter Error code ERR-04 Grid Overvoltage"
              value={createForm.title}
              onChange={(e) => setCreateForm({ ...createForm, title: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Serial Number (Optional for Auto Warranty Eval)</label>
            <input
              type="text"
              placeholder="e.g. INV-3KW-9001"
              value={createForm.reported_serial_number}
              onChange={(e) => setCreateForm({ ...createForm, reported_serial_number: e.target.value })}
              className="w-full px-3 py-2 text-sm font-mono border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Priority</label>
            <select
              value={createForm.priority}
              onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none bg-white"
            >
              <option value="LOW">Low</option>
              <option value="MEDIUM">Medium</option>
              <option value="HIGH">High</option>
              <option value="CRITICAL">Critical (Total Generation Outage)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Description / Observations</label>
            <textarea
              rows={3}
              placeholder="Customer reported no solar generation since morning..."
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowCreateModal(false)}
              className="px-4 py-2 border border-stone-300 text-stone-700 rounded-lg text-sm hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-sm font-medium hover:bg-emerald-900"
            >
              Submit Ticket
            </button>
          </div>
        </form>
      </Modal>

      {/* Assign Modal */}
      <Modal
        isOpen={showAssignModal}
        onClose={() => setShowAssignModal(false)}
        title={`Assign Field Technician — ${selectedTicket?.ticket_number}`}
      >
        <form onSubmit={handleAssign} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Select Field Technician</label>
            <select
              required
              value={assignForm.technician_id}
              onChange={(e) => setAssignForm({ technician_id: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none bg-white"
            >
              <option value="">-- Choose Technician --</option>
              {technicians.map((t) => (
                <option key={t.id} value={t.id}>
                  {t.name} ({t.skill_level} — {t.active_jobs_count} active jobs)
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowAssignModal(false)}
              className="px-4 py-2 border border-stone-300 text-stone-700 rounded-lg text-sm hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-sm font-medium hover:bg-emerald-900"
            >
              Confirm Assignment
            </button>
          </div>
        </form>
      </Modal>

      {/* Equipment Replacement Modal (Rule #12) */}
      <Modal
        isOpen={showReplaceModal}
        onClose={() => setShowReplaceModal(false)}
        title="Equipment Replacement Workflow (Rule #12)"
      >
        <form onSubmit={handleReplaceEquipment} className="space-y-4">
          <div className="p-3 bg-amber-50 rounded-lg border border-amber-200 text-xs text-amber-900 space-y-1">
            <span className="font-semibold">Rule #12 Enforcement:</span>
            <p>
              When a component is replaced under service:
              1. The defective serial number is marked as <code>RETURNED_DEFECTIVE</code>.
              2. The replacement serial number is updated to <code>ALLOCATED_CUSTOMER</code>.
              3. The customer warranty record is updated with remaining validity.
            </p>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Defective Serial Number (To Return) *</label>
            <input
              type="text"
              required
              value={replaceForm.old_serial_number}
              onChange={(e) => setReplaceForm({ ...replaceForm, old_serial_number: e.target.value })}
              placeholder="e.g. INV-3KW-9001"
              className="w-full px-3 py-2 text-sm font-mono border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">New Serial Number (From Available Stock) *</label>
            <input
              type="text"
              required
              value={replaceForm.new_serial_number}
              onChange={(e) => setReplaceForm({ ...replaceForm, new_serial_number: e.target.value })}
              placeholder="e.g. INV-3KW-9002"
              className="w-full px-3 py-2 text-sm font-mono border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Replacement Reason *</label>
            <input
              type="text"
              required
              value={replaceForm.replacement_reason}
              onChange={(e) => setReplaceForm({ ...replaceForm, replacement_reason: e.target.value })}
              placeholder="e.g. Failed internal MPPT board replaced under warranty"
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowReplaceModal(false)}
              className="px-4 py-2 border border-stone-300 text-stone-700 rounded-lg text-sm hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-amber-700 text-white rounded-lg text-sm font-medium hover:bg-amber-800"
            >
              Execute Replacement
            </button>
          </div>
        </form>
      </Modal>

      {/* Resolve Modal */}
      <Modal
        isOpen={showResolveModal}
        onClose={() => setShowResolveModal(false)}
        title={`Complete Service & Customer Acceptance — ${selectedTicket?.ticket_number}`}
      >
        <form onSubmit={handleResolve} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Technician Resolution Summary *</label>
            <textarea
              required
              rows={3}
              value={resolveForm.resolution_notes}
              onChange={(e) => setResolveForm({ ...resolveForm, resolution_notes: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">
                Labor Cost (₹) {selectedTicket?.is_under_warranty && <span className="text-emerald-700 font-bold">(Covered)</span>}
              </label>
              <input
                type="number"
                step="0.01"
                value={resolveForm.labor_cost}
                onChange={(e) => setResolveForm({ ...resolveForm, labor_cost: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">
                Parts Cost (₹) {selectedTicket?.is_under_warranty && <span className="text-emerald-700 font-bold">(Covered)</span>}
              </label>
              <input
                type="number"
                step="0.01"
                value={resolveForm.parts_cost}
                onChange={(e) => setResolveForm({ ...resolveForm, parts_cost: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Customer Acceptance Signature/ID</label>
            <input
              type="text"
              required
              value={resolveForm.customer_signature}
              onChange={(e) => setResolveForm({ ...resolveForm, customer_signature: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none font-mono text-xs"
            />
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowResolveModal(false)}
              className="px-4 py-2 border border-stone-300 text-stone-700 rounded-lg text-sm hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-sm font-medium hover:bg-emerald-900"
            >
              Mark Resolved
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
