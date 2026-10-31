import React, { useState, useEffect } from 'react';
import { Plus, User, Phone, Mail, MapPin, History, Eye, ArrowRight } from 'lucide-react';
import { customersAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const CustomersPage = () => {
  const [customers, setCustomers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedCustomer, setSelectedCustomer] = useState(null);
  const [customerHistory, setCustomerHistory] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [isCreateOpen, setIsCreateOpen] = useState(false);

  const [newCust, setNewCust] = useState({
    name: '',
    phone: '',
    email: '',
    address: '',
    city: 'Hyderabad',
    customer_type: 'Residential',
    required_capacity_kw: 3.0,
    solar_requirement: 'On-Grid',
    monthly_bill: 3000,
    subsidy_required: true,
  });

  const fetchCustomers = async () => {
    setLoading(true);
    try {
      const res = await customersAPI.getCustomers();
      setCustomers(res.data);
    } catch (err) {
      console.error('Failed to fetch customers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCustomers();
  }, []);

  const openCustomerDetail = async (cust) => {
    setSelectedCustomer(cust);
    setIsDetailOpen(true);
    try {
      const res = await customersAPI.getCustomer(cust.id);
      setCustomerHistory(res.data.history);
    } catch (err) {
      console.error('Failed to load history:', err);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      await customersAPI.createCustomer(newCust);
      setIsCreateOpen(false);
      fetchCustomers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create customer');
    }
  };

  const columns = [
    {
      header: 'Customer Name',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '700', color: 'var(--text-main)' }}>{row.name}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.email || 'No email provided'}</div>
        </div>
      ),
    },
    {
      header: 'Contact & City',
      render: (row) => (
        <div>
          <div style={{ fontSize: '13px', fontWeight: '600' }}><Phone size={12} style={{ display: 'inline' }} /> {row.phone}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-light)' }}><MapPin size={12} style={{ display: 'inline' }} /> {row.city}</div>
        </div>
      ),
    },
    {
      header: 'Address',
      accessor: 'address',
      render: (row) => (
        <span style={{ fontSize: '13px', color: 'var(--text-muted)', maxWidth: '280px', display: 'inline-block' }}>
          {row.address}
        </span>
      ),
    },
    {
      header: 'Category',
      accessor: 'customer_type',
      render: (row) => <span className="badge badge-neutral">{row.customer_type}</span>,
    },
    {
      header: 'Capacity',
      render: (row) => (
        <span style={{ fontWeight: '600' }}>
          {row.required_capacity_kw} kW {row.solar_requirement}
        </span>
      ),
    },
    {
      header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <button className="btn btn-secondary btn-sm" onClick={() => openCustomerDetail(row)}>
          <Eye size={14} /> View History
        </button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <button className="btn btn-primary" onClick={() => setIsCreateOpen(true)}>
          <Plus size={16} /> Add New Customer
        </button>
      </div>

      <DataTable
        title="Customer Master Directory"
        subtitle="Audited repository of solar customers, historical projects, warranties, and complaints"
        columns={columns}
        data={customers}
        searchKey="name"
        searchPlaceholder="Search customers by name, phone, city, address..."
      />

      {/* Customer 360-Degree Detail & History Modal */}
      <Modal isOpen={isDetailOpen} onClose={() => setIsDetailOpen(false)} title={`Customer Record: ${selectedCustomer?.name}`} maxWidth="850px">
        {selectedCustomer && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', backgroundColor: 'var(--bg-subtle)', padding: '16px', borderRadius: 'var(--radius-md)', marginBottom: '20px' }}>
              <div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Customer Name & Contact</div>
                <div style={{ fontSize: '15px', fontWeight: '700' }}>{selectedCustomer.name}</div>
                <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{selectedCustomer.phone} • {selectedCustomer.email}</div>
              </div>
              <div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Installation Site Address</div>
                <div style={{ fontSize: '13px', fontWeight: '600' }}>{selectedCustomer.address}, {selectedCustomer.city}</div>
                <div style={{ fontSize: '12px', color: 'var(--color-primary-700)', marginTop: '2px' }}>
                  Requirement: {selectedCustomer.required_capacity_kw} kW {selectedCustomer.solar_requirement}
                </div>
              </div>
            </div>

            <h4 style={{ fontSize: '15px', fontWeight: '700', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <History size={16} /> 360° Operational Relationship Timeline
            </h4>

            {/* Linked Orders */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Sales Orders ({(customerHistory?.orders || []).length})
              </div>
              {(customerHistory?.orders || []).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-light)', padding: '8px', backgroundColor: 'var(--bg-page)', borderRadius: '6px' }}>No orders placed yet</div>
              ) : (
                (customerHistory?.orders || []).map((o) => (
                  <div key={o.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', border: '1px solid var(--border-color)', borderRadius: '8px', marginBottom: '6px', fontSize: '13px' }}>
                    <div>
                      <strong>{o.ref}</strong> • ₹{o.amount?.toLocaleString()} (Advance: ₹{o.advance?.toLocaleString()})
                    </div>
                    <StatusBadge status={o.status} />
                  </div>
                ))
              )}
            </div>

            {/* Active Warranties */}
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Active Warranties ({(customerHistory?.warranties || []).length})
              </div>
              {(customerHistory?.warranties || []).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-light)', padding: '8px', backgroundColor: 'var(--bg-page)', borderRadius: '6px' }}>No active warranties registered yet</div>
              ) : (
                (customerHistory?.warranties || []).map((w) => (
                  <div key={w.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', border: '1px solid var(--border-color)', borderRadius: '8px', marginBottom: '6px', fontSize: '13px' }}>
                    <div>
                      Serial: <strong>{w.serial}</strong> (Valid until: {w.end})
                    </div>
                    <StatusBadge status={w.status} />
                  </div>
                ))
              )}
            </div>

            {/* Service Complaints */}
            <div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                After-Sales Service History ({(customerHistory?.service_tickets || []).length})
              </div>
              {(customerHistory?.service_tickets || []).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-light)', padding: '8px', backgroundColor: 'var(--bg-page)', borderRadius: '6px' }}>No service complaints reported</div>
              ) : (
                (customerHistory?.service_tickets || []).map((t) => (
                  <div key={t.id} style={{ display: 'flex', justifyContent: 'space-between', padding: '10px 14px', border: '1px solid var(--border-color)', borderRadius: '8px', marginBottom: '6px', fontSize: '13px' }}>
                    <div>
                      <strong>{t.ref}</strong>: {t.fault}
                    </div>
                    <StatusBadge status={t.status} />
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Add Customer Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Add New Customer Profile">
        <form onSubmit={handleCreate}>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Customer Name *</label>
              <input
                type="text"
                required
                className="form-control"
                value={newCust.name}
                onChange={(e) => setNewCust({ ...newCust, name: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Phone Number *</label>
              <input
                type="tel"
                required
                className="form-control"
                value={newCust.phone}
                onChange={(e) => setNewCust({ ...newCust, phone: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Email Address</label>
              <input
                type="email"
                className="form-control"
                value={newCust.email}
                onChange={(e) => setNewCust({ ...newCust, email: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">City *</label>
              <input
                type="text"
                required
                className="form-control"
                value={newCust.city}
                onChange={(e) => setNewCust({ ...newCust, city: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Full Address *</label>
            <input
              type="text"
              required
              className="form-control"
              value={newCust.address}
              onChange={(e) => setNewCust({ ...newCust, address: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Save Customer
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};



export default CustomersPage;
