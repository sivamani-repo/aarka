import React, { useState, useEffect } from 'react';
import { ShoppingCart, Eye, PackageCheck, CreditCard, Truck, CheckCircle, List } from 'lucide-react';
import { ordersAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const OrdersPage = () => {
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [isDetailOpen, setIsDetailOpen] = useState(false);
  const [picklistData, setPicklistData] = useState(null);
  const [isPicklistOpen, setIsPicklistOpen] = useState(false);

  const fetchOrders = async () => {
    setLoading(true);
    try {
      const res = await ordersAPI.getOrders();
      setOrders(res.data);
    } catch (err) {
      console.error('Failed to load orders:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchOrders();
  }, []);

  const openOrderDetail = (order) => {
    setSelectedOrder(order);
    setIsDetailOpen(true);
  };

  const openPicklist = async (order) => {
    setSelectedOrder(order);
    try {
      const res = await ordersAPI.getPicklist(order.id);
      setPicklistData(res.data);
      setIsPicklistOpen(true);
    } catch (err) {
      alert('Failed to load warehouse picklist');
    }
  };

  const handleReserve = async (orderId) => {
    try {
      await ordersAPI.reserveMaterials(orderId);
      fetchOrders();
      alert('Materials successfully reserved in warehouse for this project.');
    } catch (err) {
      alert('Failed to reserve materials');
    }
  };

  const columns = [
    {
      header: 'Order Number',
      accessor: 'order_number',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
          {row.order_number}
        </span>
      ),
    },
    {
      header: 'Customer',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '600' }}>{row.customer_name}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.customer_phone}</div>
        </div>
      ),
    },
    {
      header: 'System',
      render: (row) => (
        <div>
          <strong>{row.capacity_kw} kW</strong> • {row.package_type}
        </div>
      ),
    },
    {
      header: 'Total Value',
      render: (row) => <span style={{ fontWeight: '800' }}>₹{row.total_amount?.toLocaleString()}</span>,
    },
    {
      header: 'Paid / Advance',
      render: (row) => (
        <span style={{ fontWeight: '600', color: 'var(--color-primary-700)' }}>
          ₹{row.advance_paid?.toLocaleString()}
        </span>
      ),
    },
    {
      header: 'Balance Due',
      render: (row) => (
        <span style={{ fontWeight: '600', color: row.balance_due > 0 ? 'var(--color-rose-600)' : 'var(--color-primary-600)' }}>
          ₹{row.balance_due?.toLocaleString()}
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
        <div style={{ display: 'flex', gap: '6px' }}>
          <button className="btn btn-secondary btn-sm" onClick={() => openOrderDetail(row)}>
            <Eye size={13} /> Details
          </button>
          <button className="btn btn-secondary btn-sm" onClick={() => openPicklist(row)}>
            <List size={13} /> Picklist
          </button>
          {row.status === 'CONFIRMED' && (
            <button className="btn btn-primary btn-sm" onClick={() => handleReserve(row.id)}>
              <PackageCheck size={13} /> Reserve Stock
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <DataTable
        title="Sales Orders & Execution Tracking"
        subtitle="Agreed project contracts snapshotting BOM prices, advance requirements, and fulfillment milestones"
        columns={columns}
        data={orders}
        searchKey="order_number"
        searchPlaceholder="Search orders by number, customer..."
      />

      {/* Order Detail Modal */}
      <Modal isOpen={isDetailOpen} onClose={() => setIsDetailOpen(false)} title={`Sales Order: ${selectedOrder?.order_number}`} maxWidth="800px">
        {selectedOrder && (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', backgroundColor: 'var(--bg-subtle)', padding: '16px', borderRadius: '8px', marginBottom: '20px', fontSize: '13px' }}>
              <div>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '700' }}>Customer Information</div>
                <div style={{ fontWeight: '700', fontSize: '15px' }}>{selectedOrder.customer_name}</div>
                <div>{selectedOrder.customer_phone}</div>
                <div style={{ color: 'var(--text-muted)' }}>Site: {selectedOrder.delivery_address}</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '700' }}>Project Scope</div>
                <div style={{ fontWeight: '700', fontSize: '15px' }}>{selectedOrder.capacity_kw} kW {selectedOrder.package_type}</div>
                <div>Lifecycle Status: <StatusBadge status={selectedOrder.status} /></div>
              </div>
            </div>

            {/* Agreed Items Snapshot */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
                Contractual Items & Price Snapshot
              </div>
              <table className="aarka-table">
                <thead>
                  <tr>
                    <th>Component Name</th>
                    <th>Category</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total Price</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedOrder.items || []).map((it, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: '600' }}>{it.product_name}</td>
                      <td><span className="badge badge-neutral">{it.category}</span></td>
                      <td><strong>{it.quantity}</strong></td>
                      <td>₹{it.unit_price?.toLocaleString()}</td>
                      <td style={{ fontWeight: '700' }}>₹{it.total_price?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Recorded Payments History */}
            <div>
              <div style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
                Recorded Customer Payments ({(selectedOrder.payments || []).length})
              </div>
              {(selectedOrder.payments || []).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-muted)', padding: '10px', backgroundColor: 'var(--bg-subtle)', borderRadius: '6px' }}>
                  No payments recorded yet. Record initial advance in Payments tab.
                </div>
              ) : (
                <table className="aarka-table">
                  <thead>
                    <tr>
                      <th>Payment Ref</th>
                      <th>Method</th>
                      <th>Reference No</th>
                      <th>Amount Paid</th>
                    </tr>
                  </thead>
                  <tbody>
                    {(selectedOrder.payments || []).map((p) => (
                      <tr key={p.id}>
                        <td><strong>{p.payment_number}</strong></td>
                        <td>{p.method}</td>
                        <td>{p.reference}</td>
                        <td style={{ fontWeight: '700', color: 'var(--color-primary-700)' }}>₹{p.amount?.toLocaleString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        )}
      </Modal>

      {/* Warehouse Picklist Modal */}
      <Modal isOpen={isPicklistOpen} onClose={() => setIsPicklistOpen(false)} title={`Warehouse Material Picklist: ${selectedOrder?.order_number}`} maxWidth="750px">
        {picklistData && (
          <div>
            <div style={{ backgroundColor: 'var(--color-primary-50)', padding: '14px', borderRadius: '8px', marginBottom: '16px', fontSize: '13px' }}>
              <div><strong>Project:</strong> {picklistData.capacity_kw} kW {picklistData.package_type}</div>
              <div><strong>Customer Site:</strong> {picklistData.customer_name} ({picklistData.delivery_address})</div>
            </div>

            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--color-amber-600)', textTransform: 'uppercase', marginBottom: '8px' }}>
                ⚠️ Serialized Assets (Mandatory Barcode Scan at Dispatch)
              </div>
              <table className="aarka-table">
                <thead>
                  <tr>
                    <th>Equipment Type</th>
                    <th>Category</th>
                    <th>Quantity Required</th>
                    <th>Serial Status</th>
                  </tr>
                </thead>
                <tbody>
                  {(picklistData.serialized_items || []).map((it, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: '700' }}>{it.name}</td>
                      <td><span className="badge badge-warning">{it.category}</span></td>
                      <td><strong>{it.quantity} unit</strong></td>
                      <td><span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Scan barcode during dispatch</span></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div>
              <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '8px' }}>
                Standard BOS Hardware & Mounting Structures
              </div>
              <table className="aarka-table">
                <thead>
                  <tr>
                    <th>Material Description</th>
                    <th>Category</th>
                    <th>Quantity to Pick</th>
                  </tr>
                </thead>
                <tbody>
                  {(picklistData.standard_items || []).map((it, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: '600' }}>{it.name}</td>
                      <td><span className="badge badge-neutral">{it.category}</span></td>
                      <td><strong>{it.quantity}</strong></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};



export default OrdersPage;
