import React, { useState, useEffect } from 'react';
import { Plus, Truck, CheckCircle, PackageCheck, Barcode, Calendar, AlertCircle } from 'lucide-react';
import { dispatchesAPI, ordersAPI, serialsAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const DispatchPage = () => {
  const [dispatches, setDispatches] = useState([]);
  const [confirmedOrders, setConfirmedOrders] = useState([]);
  const [availableSerials, setAvailableSerials] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isConfirmOpen, setIsConfirmOpen] = useState(false);
  const [selectedDispatch, setSelectedDispatch] = useState(null);

  // Forms
  const [newDispatch, setNewDispatch] = useState({
    order_id: '',
    delivery_reference: '',
    dispatch_date: new Date().toISOString().split('T')[0],
    dispatched_by: 'Venkat Rao (Warehouse Mgr)',
    serial_numbers_input: '',
    notes: '',
  });

  const [confirmData, setConfirmData] = useState({
    delivery_date: new Date().toISOString().split('T')[0],
    delivery_proof_url: '',
    customer_confirmed: true,
    notes: 'Signed delivery challan verified by transport driver.',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [dispRes, ordRes, serRes] = await Promise.all([
        dispatchesAPI.getDispatches(),
        ordersAPI.getOrders({ status: 'READY_FOR_DISPATCH' }),
        serialsAPI.getSerials({ status: 'AVAILABLE' }),
      ]);
      setDispatches(dispRes.data);
      setConfirmedOrders(ordRes.data);
      setAvailableSerials(serRes.data);
      if (ordRes.data.length > 0) {
        setNewDispatch((prev) => ({ ...prev, order_id: ordRes.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load dispatches:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateDispatch = async (e) => {
    e.preventDefault();
    try {
      const serials = newDispatch.serial_numbers_input
        ? newDispatch.serial_numbers_input.split('\n').map((s) => s.trim().toUpperCase()).filter(Boolean)
        : [];

      await dispatchesAPI.createDispatch({
        order_id: parseInt(newDispatch.order_id),
        delivery_reference: newDispatch.delivery_reference || undefined,
        dispatch_date: newDispatch.dispatch_date,
        dispatched_by: newDispatch.dispatched_by,
        serial_numbers: serials,
        notes: newDispatch.notes,
      });

      setIsCreateOpen(false);
      fetchData();
      alert('Warehouse dispatch successfully initiated! Stock deducted and order updated.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Dispatch failed');
    }
  };

  const handleConfirmDelivery = async (e) => {
    e.preventDefault();
    if (!selectedDispatch) return;
    try {
      const res = await dispatchesAPI.confirmDelivery(selectedDispatch.id, confirmData);
      setIsConfirmOpen(false);
      fetchData();
      alert(
        `Delivery confirmed.\n\n${res.data.message}\nWarranties pending manufacturer-term verification: ${
          res.data.warranties_pending_activation?.join(', ') || 'none'
        }`
      );
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to confirm delivery');
    }
  };

  const columns = [
    {
      header: 'Delivery Ref',
      accessor: 'delivery_reference',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
          {row.delivery_reference}
        </span>
      ),
    },
    {
      header: 'Sales Order',
      accessor: 'order_number',
      render: (row) => <strong>{row.order_number}</strong>,
    },
    {
      header: 'Customer',
      accessor: 'customer_name',
      render: (row) => <span style={{ fontWeight: '600' }}>{row.customer_name}</span>,
    },
    {
      header: 'Stock Before / Dispatched / Remaining',
      render: (row) => row.stock_lines?.length ? (
        <div style={{ display: 'grid', gap: '4px', fontSize: '12px' }}>
          {row.stock_lines.map((line) => (
            <span key={line.product_id}>
              {line.product_name}: {line.previous_stock ?? 'Not recorded'} / {line.dispatched_quantity} / {line.remaining_stock ?? 'Not recorded'}
            </span>
          ))}
        </div>
      ) : <span style={{ color: 'var(--text-muted)' }}>No stock snapshot recorded</span>,
    },
    {
      header: 'Dispatched Serials',
      render: (row) => {
        let serialsList = [];
        try {
          serialsList = JSON.parse(row.serial_numbers || '[]');
        } catch (e) {
          serialsList = [];
        }
        return (
          <div style={{ display: 'flex', gap: '4px', flexWrap: 'wrap' }}>
            {serialsList.map((sn, idx) => (
              <span key={idx} className="badge badge-warning" style={{ fontSize: '11px' }}>
                <Barcode size={10} style={{ display: 'inline' }} /> {sn}
              </span>
            ))}
          </div>
        );
      },
    },
    {
      header: 'Dispatch Date',
      accessor: 'dispatch_date',
    },
    {
      header: 'Delivery Date',
      render: (row) => <span>{row.delivery_date || 'In Transit'}</span>,
    },
    {
      header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <div>
          {row.status === 'DISPATCHED' && (
            <button
              className="btn btn-primary btn-sm"
              onClick={() => {
                setSelectedDispatch(row);
                setIsConfirmOpen(true);
              }}
            >
              <CheckCircle size={13} /> Confirm Delivery (Activate Warranty)
            </button>
          )}
          {row.status === 'DELIVERED' && (
            <span style={{ fontSize: '12px', color: 'var(--color-primary-600)', fontWeight: '700' }}>
              Delivered & Active ✓
            </span>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <button className="btn btn-primary" onClick={() => setIsCreateOpen(true)}>
          <Plus size={16} /> Create Warehouse Dispatch
        </button>
      </div>

      <DataTable
        title="Warehouse Dispatch & Delivery Confirmation"
        subtitle="Serialized equipment is checked before dispatch; confirmed delivery records warranties pending certificate verification"
        columns={columns}
        data={dispatches}
        searchKey="delivery_reference"
        searchPlaceholder="Search dispatches by delivery reference, order..."
      />

      {/* Create Dispatch Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Create Warehouse Dispatch Challan">
        <form onSubmit={handleCreateDispatch}>
          <div className="form-group">
            <label className="form-label">Select Sales Order to Dispatch *</label>
            <select
              className="form-select"
              required
              value={newDispatch.order_id}
              onChange={(e) => setNewDispatch({ ...newDispatch, order_id: e.target.value })}
            >
              {confirmedOrders.length === 0 ? (
                <option value="">-- No orders currently ready for dispatch (Require advance payment) --</option>
              ) : (
                confirmedOrders.map((o) => (
                  <option key={o.id} value={o.id}>
                    {o.order_number} - {o.customer_name} ({o.capacity_kw}kW {o.package_type})
                  </option>
                ))
              )}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Delivery Challan Reference</label>
              <input
                type="text"
                className="form-control"
                placeholder="Leave blank to auto-generate DISP-2026-XXXX"
                value={newDispatch.delivery_reference}
                onChange={(e) => setNewDispatch({ ...newDispatch, delivery_reference: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Dispatch Date *</label>
              <input
                type="date"
                required
                className="form-control"
                value={newDispatch.dispatch_date}
                onChange={(e) => setNewDispatch({ ...newDispatch, dispatch_date: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Scan Serial Numbers Allocated (Mandatory for Inverter & Battery) *</label>
            <textarea
              rows={3}
              required
              className="form-textarea"
              placeholder="e.g.&#10;INV-3KW-9001&#10;BAT-150AH-8001"
              value={newDispatch.serial_numbers_input}
              onChange={(e) => setNewDispatch({ ...newDispatch, serial_numbers_input: e.target.value })}
            />
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
              Available inverters in warehouse: {availableSerials.slice(0, 4).map((s) => s.serial_number).join(', ')}
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Transport Driver & Dispatch Notes</label>
            <textarea
              rows={2}
              className="form-textarea"
              placeholder="Dispatched via Tata Ace (TS 09 UA 1234) • Driver: Ramesh"
              value={newDispatch.notes}
              onChange={(e) => setNewDispatch({ ...newDispatch, notes: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={confirmedOrders.length === 0}>
              Verify Picklist & Dispatch Equipment
            </button>
          </div>
        </form>
      </Modal>

      {/* Confirm Delivery Modal */}
      <Modal isOpen={isConfirmOpen} onClose={() => setIsConfirmOpen(false)} title={`Confirm Delivery: ${selectedDispatch?.delivery_reference}`}>
        <form onSubmit={handleConfirmDelivery}>
          <div style={{ backgroundColor: 'var(--color-primary-50)', padding: '14px', borderRadius: '8px', marginBottom: '16px', fontSize: '13px' }}>
            <div><strong>Order:</strong> {selectedDispatch?.order_number}</div>
            <div><strong>Customer:</strong> {selectedDispatch?.customer_name}</div>
            <div style={{ marginTop: '4px', color: 'var(--color-primary-800)', fontWeight: '600' }}>
              Delivery records the warranty period. Activation requires an uploaded manufacturer certificate and approval after customer-accepted installation.
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Actual Customer Delivery Date *</label>
            <input
              type="date"
              required
              className="form-control"
              value={confirmData.delivery_date}
              onChange={(e) => setConfirmData({ ...confirmData, delivery_date: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Delivery Proof URL / Signed Challan</label>
            <input
              type="text"
              className="form-control"
              placeholder="/api/uploads/dispatches/signed_challan_01.jpg"
              value={confirmData.delivery_proof_url}
              onChange={(e) => setConfirmData({ ...confirmData, delivery_proof_url: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '14px', fontWeight: '600', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={confirmData.customer_confirmed}
                onChange={(e) => setConfirmData({ ...confirmData, customer_confirmed: e.target.checked })}
                style={{ width: '18px', height: '18px', accentColor: 'var(--color-primary-700)' }}
              />
              <span>Customer site verified, all materials accepted without transit damage.</span>
            </label>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsConfirmOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              <CheckCircle size={16} /> Confirm Delivery & Activate Warranties
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};



export default DispatchPage;
