import React, { useState, useEffect } from 'react';
import { Truck, Plus, Search, Building2, Phone, Mail, FileText, CheckCircle } from 'lucide-react';
import { suppliersApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';
import DataTable from '../../components/common/DataTable';
import Modal from '../../components/common/Modal';

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const [form, setForm] = useState({
    name: '',
    contact_person: '',
    email: '',
    phone: '',
    address: '',
    gstin: '',
    payment_terms: 'NET_30',
    categories_supplied: 'SOLAR_PANELS,INVERTERS'
  });

  const fetchSuppliers = async () => {
    try {
      setLoading(true);
      const res = await suppliersApi.getAll();
      setSuppliers(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await suppliersApi.create(form);
      setFeedback({ type: 'success', msg: `Supplier "${form.name}" added successfully.` });
      setShowModal(false);
      setForm({
        name: '',
        contact_person: '',
        email: '',
        phone: '',
        address: '',
        gstin: '',
        payment_terms: 'NET_30',
        categories_supplied: 'SOLAR_PANELS,INVERTERS'
      });
      fetchSuppliers();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Failed to add supplier' });
    }
  };

  const filtered = suppliers.filter(s => 
    s.name?.toLowerCase().includes(search.toLowerCase()) ||
    s.contact_person?.toLowerCase().includes(search.toLowerCase()) ||
    s.gstin?.toLowerCase().includes(search.toLowerCase())
  );

  const columns = [
    {
      header: 'Supplier Name',
      accessor: 'name',
      cell: (row) => (
        <div>
          <div className="font-semibold text-stone-900">{row.name}</div>
          <div className="text-xs text-stone-500 flex items-center gap-1 mt-0.5">
            <Building2 className="w-3 h-3 text-stone-400" />
            GSTIN: <span className="font-mono text-emerald-800">{row.gstin || 'N/A'}</span>
          </div>
        </div>
      )
    },
    {
      header: 'Contact Person',
      accessor: 'contact_person',
      cell: (row) => (
        <div>
          <div className="text-sm font-medium text-stone-800">{row.contact_person || 'N/A'}</div>
          <div className="text-xs text-stone-500 flex items-center gap-2 mt-0.5">
            {row.phone && <span className="flex items-center gap-1"><Phone className="w-3 h-3" /> {row.phone}</span>}
            {row.email && <span className="flex items-center gap-1"><Mail className="w-3 h-3" /> {row.email}</span>}
          </div>
        </div>
      )
    },
    {
      header: 'Supplied Categories',
      accessor: 'categories_supplied',
      cell: (row) => (
        <div className="flex flex-wrap gap-1">
          {(row.categories_supplied || '').split(',').map((cat, idx) => (
            <span key={idx} className="text-[11px] bg-stone-100 text-stone-700 px-2 py-0.5 rounded font-medium">
              {cat.trim()}
            </span>
          ))}
        </div>
      )
    },
    {
      header: 'Payment Terms',
      accessor: 'payment_terms',
      cell: (row) => (
        <span className="text-xs px-2 py-1 bg-emerald-50 text-emerald-800 rounded font-mono font-medium">
          {row.payment_terms || 'NET_30'}
        </span>
      )
    },
    {
      header: 'Status',
      accessor: 'is_active',
      cell: (row) => (
        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${
          row.is_active ? 'bg-emerald-100 text-emerald-800' : 'bg-stone-100 text-stone-600'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${row.is_active ? 'bg-emerald-600' : 'bg-stone-400'}`}></span>
          {row.is_active ? 'Active' : 'Inactive'}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Component Suppliers & Vendors</h1>
          <p className="text-sm text-stone-600 mt-1">
            Manage Tier-1 OEM suppliers for PV modules, hybrid inverters, batteries, and mounting hardware.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Supplier
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
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Total Suppliers" value={suppliers.length} icon={Building2} subtitle="Verified vendor partners" />
        <StatCard title="Active Vendors" value={suppliers.filter(s => s.is_active).length} icon={CheckCircle} subtitle="Supplying materials" />
        <StatCard title="Active Categories" value="4 Core" icon={Truck} subtitle="Panels, Inverters, Structures, Electrical" />
      </div>

      {/* Search */}
      <div className="bg-white p-4 rounded-xl border border-stone-200 flex items-center justify-between shadow-sm">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search vendor name, GSTIN, contact..."
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
        emptyMessage="No suppliers registered yet."
      />

      {/* Add Supplier Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Register New Solar Equipment Supplier"
      >
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Company / Vendor Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. Waaree Energies Ltd."
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Contact Person</label>
              <input
                type="text"
                placeholder="e.g. Mr. Rajesh Sharma"
                value={form.contact_person}
                onChange={(e) => setForm({ ...form, contact_person: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Phone Number</label>
              <input
                type="text"
                placeholder="+91 98765 43210"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Email</label>
              <input
                type="email"
                placeholder="sales@vendor.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">GSTIN Number</label>
              <input
                type="text"
                placeholder="27AABCU9603R1ZM"
                value={form.gstin}
                onChange={(e) => setForm({ ...form, gstin: e.target.value })}
                className="w-full px-3 py-2 text-sm font-mono border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Supplied Categories</label>
            <input
              type="text"
              placeholder="e.g. SOLAR_PANELS, INVERTERS, MOUNTING_STRUCTURE"
              value={form.categories_supplied}
              onChange={(e) => setForm({ ...form, categories_supplied: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Payment Terms</label>
              <select
                value={form.payment_terms}
                onChange={(e) => setForm({ ...form, payment_terms: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none bg-white"
              >
                <option value="IMMEDIATE">Immediate Advance</option>
                <option value="NET_15">Net 15 Days</option>
                <option value="NET_30">Net 30 Days</option>
                <option value="NET_60">Net 60 Days</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Warehouse / City Address</label>
              <input
                type="text"
                placeholder="Surat, Gujarat"
                value={form.address}
                onChange={(e) => setForm({ ...form, address: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={() => setShowModal(false)}
              className="px-4 py-2 border border-stone-300 text-stone-700 rounded-lg text-sm hover:bg-stone-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-emerald-800 text-white rounded-lg text-sm font-medium hover:bg-emerald-900"
            >
              Save Supplier
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
