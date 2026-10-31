import React, { useState, useEffect } from 'react';
import { Users, Plus, Shield, Mail, Phone, CheckCircle, Search, UserCheck } from 'lucide-react';
import { authApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';
import DataTable from '../../components/common/DataTable';
import Modal from '../../components/common/Modal';

export default function TeamPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'Sales Representative',
    phone: ''
  });

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const res = await authApi.getUsers();
      setUsers(res.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleCreateUser = async (e) => {
    e.preventDefault();
    try {
      await authApi.createUser(form);
      setFeedback({ type: 'success', msg: `Team member ${form.name} created successfully.` });
      setShowModal(false);
      setForm({ name: '', email: '', password: '', role: 'Sales Representative', phone: '' });
      fetchUsers();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Failed to create user' });
    }
  };

  const filtered = users.filter(u =>
    u.name?.toLowerCase().includes(search.toLowerCase()) ||
    u.email?.toLowerCase().includes(search.toLowerCase()) ||
    u.role?.toLowerCase().includes(search.toLowerCase())
  );

  const columns = [
    {
      header: 'Staff Member',
      accessor: 'name',
      cell: (row) => (
        <div>
          <div className="font-semibold text-stone-900">{row.name}</div>
          <div className="text-xs text-stone-500 flex items-center gap-2 mt-0.5">
            <span className="flex items-center gap-1"><Mail className="w-3 h-3 text-stone-400" /> {row.email}</span>
            {row.phone && <span className="flex items-center gap-1"><Phone className="w-3 h-3 text-stone-400" /> {row.phone}</span>}
          </div>
        </div>
      )
    },
    {
      header: 'Enterprise Role',
      accessor: 'role',
      cell: (row) => {
        let badgeColor = 'bg-stone-100 text-stone-700';
        if (row.role === 'Director / Admin') badgeColor = 'bg-emerald-900 text-emerald-100';
        else if (row.role === 'Sales Representative') badgeColor = 'bg-blue-100 text-blue-800';
        else if (row.role === 'Site Surveyor') badgeColor = 'bg-teal-100 text-teal-800';
        else if (row.role === 'Warehouse Manager') badgeColor = 'bg-amber-100 text-amber-900';
        else if (row.role === 'Installation Engineer') badgeColor = 'bg-emerald-100 text-emerald-800';
        else if (row.role === 'Service Coordinator') badgeColor = 'bg-indigo-100 text-indigo-800';
        else if (row.role === 'Finance / Accounts') badgeColor = 'bg-purple-100 text-purple-800';

        return (
          <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-medium ${badgeColor}`}>
            <Shield className="w-3 h-3" />
            {row.role}
          </span>
        );
      }
    },
    {
      header: 'Account Status',
      accessor: 'is_active',
      cell: (row) => (
        <span className={`inline-flex items-center gap-1 text-xs px-2 py-0.5 rounded-full font-medium ${
          row.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-rose-50 text-rose-700'
        }`}>
          <span className={`w-1.5 h-1.5 rounded-full ${row.is_active ? 'bg-emerald-600' : 'bg-rose-600'}`}></span>
          {row.is_active ? 'Active' : 'Deactivated'}
        </span>
      )
    },
    {
      header: 'Joined Date',
      accessor: 'created_at',
      cell: (row) => (
        <span className="text-xs text-stone-500 font-mono">
          {new Date(row.created_at).toLocaleDateString()}
        </span>
      )
    }
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Team Management & RBAC Permissions</h1>
          <p className="text-sm text-stone-600 mt-1">
            Manage user accounts, internal department assignments, and system authorization roles.
          </p>
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-800 hover:bg-emerald-900 text-white text-sm font-medium rounded-lg shadow-sm transition-colors"
        >
          <Plus className="w-4 h-4" />
          Add Team Member
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
        <StatCard title="Total Staff" value={users.length} icon={Users} subtitle="Registered platform users" />
        <StatCard title="Active Accounts" value={users.filter(u => u.is_active).length} icon={UserCheck} subtitle="Authorized for sign-in" />
        <StatCard title="Departments" value="7 Roles" icon={Shield} subtitle="Strict RBAC segregation" />
      </div>

      {/* Search */}
      <div className="bg-white p-4 rounded-xl border border-stone-200 flex items-center justify-between shadow-sm">
        <div className="relative w-full sm:w-80">
          <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search team member name, role, email..."
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
        emptyMessage="No team members found."
      />

      {/* Add User Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => setShowModal(false)}
        title="Create Team Member Account"
      >
        <form onSubmit={handleCreateUser} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Full Name *</label>
            <input
              type="text"
              required
              placeholder="e.g. Anand Kumar"
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Email Address *</label>
              <input
                type="email"
                required
                placeholder="anand@aarka.com"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Phone Number</label>
              <input
                type="text"
                placeholder="+91 98765 11223"
                value={form.phone}
                onChange={(e) => setForm({ ...form, phone: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Assigned Role *</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none bg-white"
              >
                <option value="Director / Admin">Director / Admin</option>
                <option value="Sales Representative">Sales Representative</option>
                <option value="Site Surveyor">Site Surveyor</option>
                <option value="Warehouse Manager">Warehouse Manager</option>
                <option value="Installation Engineer">Installation Engineer</option>
                <option value="Service Coordinator">Service Coordinator</option>
                <option value="Finance / Accounts">Finance / Accounts</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Initial Password *</label>
              <input
                type="password"
                required
                placeholder="••••••••"
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
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
              Create Account
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
