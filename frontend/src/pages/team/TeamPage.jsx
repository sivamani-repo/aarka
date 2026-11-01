import React, { useState, useEffect } from 'react';
import { Users, Plus, Shield, Mail, Phone, Search, UserCheck, Pencil, UserX, UserRoundCheck } from 'lucide-react';
import { authApi } from '../../services/api';
import StatCard from '../../components/common/StatCard';
import DataTable from '../../components/common/DataTable';
import Modal from '../../components/common/Modal';

export default function TeamPage() {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [permissionOptions, setPermissionOptions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [feedback, setFeedback] = useState(null);

  const [form, setForm] = useState({
    name: '',
    email: '',
    password: '',
    role: 'Sales Executive',
    phone: '',
    reporting_manager_id: '',
    permissions: [],
  });

  const fetchUsers = async () => {
    try {
      setLoading(true);
      const [usersResponse, rolesResponse, permissionsResponse] = await Promise.all([
        authApi.getUsers(),
        authApi.getRoles(),
        authApi.getPermissions(),
      ]);
      setUsers(usersResponse.data);
      setRoles(rolesResponse.data);
      setPermissionOptions(permissionsResponse.data);
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Could not load employee administration data.' });
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
      if (editingUser) {
        await authApi.updateUser(editingUser.id, {
          name: form.name,
          email: form.email,
          role: form.role,
          phone: form.phone,
          reporting_manager_id: form.reporting_manager_id ? Number(form.reporting_manager_id) : null,
          permissions: form.permissions,
        });
      } else {
        await authApi.createUser({
          ...form,
          reporting_manager_id: form.reporting_manager_id ? Number(form.reporting_manager_id) : null,
        });
      }
      setFeedback({
        type: 'success',
        msg: `Team member ${form.name} ${editingUser ? 'updated' : 'created'} successfully.`,
      });
      setShowModal(false);
      setEditingUser(null);
      setForm({
        name: '',
        email: '',
        password: '',
        role: 'Sales Executive',
        phone: '',
        reporting_manager_id: '',
        permissions: [],
      });
      fetchUsers();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || `Failed to ${editingUser ? 'update' : 'create'} employee.` });
    }
  };

  const openEditUser = (employee) => {
    setEditingUser(employee);
    setForm({
      name: employee.name || '',
      email: employee.email || '',
      password: '',
      role: employee.role,
      phone: employee.phone || '',
      reporting_manager_id: employee.reporting_manager_id ? String(employee.reporting_manager_id) : '',
      permissions: (employee.additional_permissions || []).map(({ resource, action }) => `${resource}:${action}`),
    });
    setShowModal(true);
  };

  const toggleAccountStatus = async (employee) => {
    try {
      await authApi.updateUser(employee.id, { is_active: !employee.is_active });
      setFeedback({ type: 'success', msg: `${employee.name}'s account is now ${employee.is_active ? 'deactivated' : 'active'}.` });
      fetchUsers();
    } catch (err) {
      setFeedback({ type: 'error', msg: err.response?.data?.detail || 'Could not update the account status.' });
    }
  };

  const managers = users.filter((employee) =>
    employee.role === 'Director / Super Admin' || employee.role.endsWith('Manager')
  );
  const permissionsByResource = permissionOptions.reduce((groups, permission) => {
    groups[permission.resource] = [...(groups[permission.resource] || []), permission.action];
    return groups;
  }, {});

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
          <div className="text-xs text-emerald-800 font-medium mt-0.5">
            {row.employee_id || 'Employee ID pending'}
          </div>
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
        if (row.role === 'Director / Super Admin') badgeColor = 'bg-emerald-900 text-emerald-100';
        else if (row.role === 'Sales Executive' || row.role === 'Sales Manager') badgeColor = 'bg-blue-100 text-blue-800';
        else if (row.role === 'Site Survey Engineer') badgeColor = 'bg-teal-100 text-teal-800';
        else if (row.role === 'Warehouse Manager') badgeColor = 'bg-amber-100 text-amber-900';
        else if (row.role === 'Installation Manager' || row.role === 'Solar Technician') badgeColor = 'bg-emerald-100 text-emerald-800';
        else if (row.role === 'Service Manager' || row.role === 'Support Executive') badgeColor = 'bg-indigo-100 text-indigo-800';
        else if (row.role === 'Finance Manager') badgeColor = 'bg-purple-100 text-purple-800';

        return (
          <span className={`inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full font-medium ${badgeColor}`}>
            <Shield className="w-3 h-3" />
            {row.role}
          </span>
        );
      }
    },
    {
      header: 'Department',
      accessor: 'department',
      cell: (row) => <span className="text-sm text-stone-700">{row.department || '—'}</span>,
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
    },
    {
      header: 'Manage',
      accessor: 'id',
      cell: (row) => (
        <div className="flex items-center gap-2">
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => openEditUser(row)}
            title={`Edit ${row.name}`}
          >
            <Pencil size={14} /> Edit
          </button>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={() => toggleAccountStatus(row)}
            title={row.is_active ? 'Deactivate employee' : 'Reactivate employee'}
          >
            {row.is_active ? <UserX size={14} /> : <UserRoundCheck size={14} />}
          </button>
        </div>
      )
    }
  ];

  return (
    <div className="space-y-6 enterprise-page enterprise-team-page">
      {/* Header */}
      <div className="enterprise-page-header">
        <div className="enterprise-page-copy">
          <span className="enterprise-eyebrow">Administration · Access control</span>
          <h1 className="text-2xl font-bold text-stone-900 tracking-tight">Team Management & RBAC Permissions</h1>
          <p className="text-sm text-stone-600 mt-1">
            Manage user accounts, internal department assignments, and system authorization roles.
          </p>
        </div>
        <button
          onClick={() => {
            setEditingUser(null);
            setForm({
              name: '',
              email: '',
              password: '',
              role: 'Sales Executive',
              phone: '',
              reporting_manager_id: '',
              permissions: [],
            });
            setShowModal(true);
          }}
          className="btn btn-glass"
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
      <div className="enterprise-kpi-grid grid grid-cols-1 sm:grid-cols-3 gap-4">
        <StatCard title="Total Staff" value={users.length} icon={Users} subtext="Registered platform users" />
        <StatCard title="Active Accounts" value={users.filter(u => u.is_active).length} icon={UserCheck} subtext="Authorized for sign-in" />
        <StatCard title="Departments & Roles" value={`${new Set(roles.map((role) => role.department)).size} / ${roles.length}`} icon={Shield} subtext="Configured departments and job roles" />
      </div>

      {/* Search */}
      <div className="enterprise-list-toolbar">
        <div>
          <div className="enterprise-toolbar-title">People directory</div>
          <p className="enterprise-toolbar-description">Manage staff profiles, department access, and account status.</p>
        </div>
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
        {search && (
          <button
            type="button"
            onClick={() => setSearch('')}
            className="enterprise-clear-filter"
          >
            Clear search
          </button>
        )}
      </div>

      <DataTable
        className="enterprise-table-card"
        title="Team directory"
        subtitle="Employee accounts and access roles"
        columns={columns}
        data={filtered}
        loading={loading}
        emptyMessage="No team members found."
      />

      {/* Add User Modal */}
      <Modal
        isOpen={showModal}
        onClose={() => {
          setShowModal(false);
          setEditingUser(null);
        }}
        title={editingUser ? 'Update Employee Profile' : 'Create Employee Account'}
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
                {roles.map((role) => (
                  <option value={role.name} key={role.name}>{role.name}</option>
                ))}
              </select>
              <span className="mt-1 block text-xs text-stone-500">
                Department: {roles.find((role) => role.name === form.role)?.department || 'Select a role'}
              </span>
            </div>
            <div>
              <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">
                {editingUser ? 'Set new password separately' : 'Initial Password *'}
              </label>
              <input
                type="password"
                required={!editingUser}
                disabled={!!editingUser}
                placeholder={editingUser ? 'Use password reset workflow' : 'At least 8 characters'}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-stone-700 uppercase mb-1">Reporting Manager</label>
            <select
              value={form.reporting_manager_id}
              onChange={(e) => setForm({ ...form, reporting_manager_id: e.target.value })}
              className="w-full px-3 py-2 text-sm border border-stone-300 rounded-lg focus:ring-2 focus:ring-emerald-600 outline-none bg-white"
            >
              <option value="">No reporting manager assigned</option>
              {managers.filter((manager) => manager.id !== editingUser?.id).map((manager) => (
                <option key={manager.id} value={manager.id}>
                  {manager.name} · {manager.role}
                </option>
              ))}
            </select>
          </div>

          <details className="rounded-lg border border-stone-200 bg-stone-50 p-3">
            <summary className="cursor-pointer text-sm font-semibold text-stone-800">
              Additional permissions
              <span className="ml-2 text-xs font-normal text-stone-500">
                Optional role-independent grants
              </span>
            </summary>
            <div className="mt-3 max-h-64 space-y-3 overflow-y-auto pr-2">
              {Object.entries(permissionsByResource).map(([resource, actions]) => (
                <fieldset key={resource} className="rounded-md border border-stone-200 bg-white p-3">
                  <legend className="px-1 text-xs font-bold uppercase text-stone-700">{resource}</legend>
                  <div className="flex flex-wrap gap-x-4 gap-y-2">
                    {actions.map((action) => {
                      const permission = `${resource}:${action}`;
                      return (
                        <label key={permission} className="inline-flex items-center gap-1.5 text-xs text-stone-700">
                          <input
                            type="checkbox"
                            checked={form.permissions.includes(permission)}
                            onChange={(event) => setForm({
                              ...form,
                              permissions: event.target.checked
                                ? [...form.permissions, permission]
                                : form.permissions.filter((value) => value !== permission),
                            })}
                          />
                          {action}
                        </label>
                      );
                    })}
                  </div>
                </fieldset>
              ))}
            </div>
          </details>

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
              {editingUser ? 'Save Employee' : 'Create Account'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
