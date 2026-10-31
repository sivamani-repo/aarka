import React, { useState, useEffect } from 'react';
import { Plus, CreditCard, CheckCircle, Printer, FileText, AlertCircle, ArrowUpRight } from 'lucide-react';
import { paymentsAPI, ordersAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const PaymentsPage = () => {
  const [payments, setPayments] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isRecordOpen, setIsRecordOpen] = useState(false);
  const [isReceiptOpen, setIsReceiptOpen] = useState(false);
  const [selectedPayment, setSelectedPayment] = useState(null);

  // Form
  const [newPayment, setNewPayment] = useState({
    order_id: '',
    amount: '',
    method: 'UPI',
    reference: '',
    payment_date: new Date().toISOString().split('T')[0],
    notes: '',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [payRes, ordRes] = await Promise.all([
        paymentsAPI.getPayments(),
        ordersAPI.getOrders(),
      ]);
      setPayments(payRes.data);
      setOrders(ordRes.data);
      if (ordRes.data.length > 0) {
        setNewPayment((prev) => ({ ...prev, order_id: ordRes.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load payments:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const selectedOrderInfo = orders.find((o) => o.id === parseInt(newPayment.order_id));

  const handleRecordPayment = async (e) => {
    e.preventDefault();
    if (!selectedOrderInfo) return;
    try {
      await paymentsAPI.recordPayment({
        order_id: selectedOrderInfo.id,
        customer_id: selectedOrderInfo.customer_id,
        amount: parseFloat(newPayment.amount),
        method: newPayment.method,
        reference: newPayment.reference,
        payment_date: newPayment.payment_date,
        notes: newPayment.notes,
      });
      setIsRecordOpen(false);
      fetchData();
      alert('Payment successfully recorded and allocated to Sales Order!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to record payment');
    }
  };

  const openReceipt = (payment) => {
    setSelectedPayment(payment);
    setIsReceiptOpen(true);
  };

  const columns = [
    {
      header: 'Payment Receipt',
      accessor: 'payment_number',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
          {row.payment_number}
        </span>
      ),
    },
    {
      header: 'Customer',
      accessor: 'customer_name',
      render: (row) => <span style={{ fontWeight: '600' }}>{row.customer_name}</span>,
    },
    {
      header: 'Linked Order',
      accessor: 'order_number',
      render: (row) => (
        <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-muted)' }}>
          {row.order_number}
        </span>
      ),
    },
    {
      header: 'Amount Paid',
      render: (row) => (
        <span style={{ fontWeight: '800', color: 'var(--color-primary-700)', fontSize: '15px' }}>
          ₹{row.amount?.toLocaleString()}
        </span>
      ),
    },
    {
      header: 'Method',
      accessor: 'method',
      render: (row) => <span className="badge badge-neutral">{row.method}</span>,
    },
    {
      header: 'Transaction Ref',
      accessor: 'reference',
      render: (row) => <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.reference || '—'}</span>,
    },
    {
      header: 'Date',
      accessor: 'payment_date',
    },
    {
      header: 'Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Actions',
      render: (row) => (
        <button className="btn btn-secondary btn-sm" onClick={() => openReceipt(row)}>
          <FileText size={13} /> Receipt
        </button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <button className="btn btn-primary" onClick={() => setIsRecordOpen(true)}>
          <Plus size={16} /> Record Customer Payment
        </button>
      </div>

      <DataTable
        title="Accounts Receivable & Verified Collections"
        subtitle="MANDATORY RULE: Payments strictly audited; Cannot exceed total contract payable"
        columns={columns}
        data={payments}
        searchKey="payment_number"
        searchPlaceholder="Search payments by receipt number, customer..."
      />

      {/* Record Payment Modal */}
      <Modal isOpen={isRecordOpen} onClose={() => setIsRecordOpen(false)} title="Record Customer Payment">
        <form onSubmit={handleRecordPayment}>
          <div className="form-group">
            <label className="form-label">Select Sales Order *</label>
            <select
              className="form-select"
              required
              value={newPayment.order_id}
              onChange={(e) => setNewPayment({ ...newPayment, order_id: e.target.value })}
            >
              {orders.map((o) => (
                <option key={o.id} value={o.id}>
                  {o.order_number} - {o.customer_name} (Balance Due: ₹{o.balance_due?.toLocaleString()})
                </option>
              ))}
            </select>
          </div>

          {selectedOrderInfo && (
            <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '14px', borderRadius: '8px', marginBottom: '16px', fontSize: '13px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span>Contract Total:</span>
                <strong>₹{selectedOrderInfo.total_amount?.toLocaleString()}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px', color: 'var(--color-primary-700)' }}>
                <span>Previously Paid:</span>
                <strong>₹{selectedOrderInfo.advance_paid?.toLocaleString()}</strong>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', borderTop: '1px solid var(--border-color)', paddingTop: '6px', fontWeight: '700', color: 'var(--color-rose-600)' }}>
                <span>Outstanding Balance Due:</span>
                <span>₹{selectedOrderInfo.balance_due?.toLocaleString()}</span>
              </div>
            </div>
          )}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Payment Amount (₹) *</label>
              <input
                type="number"
                required
                max={selectedOrderInfo?.balance_due}
                placeholder={`Max ₹${selectedOrderInfo?.balance_due || 0}`}
                className="form-control"
                value={newPayment.amount}
                onChange={(e) => setNewPayment({ ...newPayment, amount: e.target.value })}
              />
              <p style={{ fontSize: '11px', color: 'var(--text-light)', marginTop: '4px' }}>
                Enforces Rule #16: Payment cannot exceed balance due of ₹{selectedOrderInfo?.balance_due?.toLocaleString()}.
              </p>
            </div>

            <div className="form-group">
              <label className="form-label">Payment Mode *</label>
              <select
                className="form-select"
                value={newPayment.method}
                onChange={(e) => setNewPayment({ ...newPayment, method: e.target.value })}
              >
                <option value="UPI">UPI (GooglePay / PhonePe / Paytm)</option>
                <option value="Bank Transfer">Bank Transfer (NEFT / RTGS / IMPS)</option>
                <option value="Cash">Cash Receipt</option>
                <option value="Cheque">Cheque</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Bank Transaction UTR / Ref Number *</label>
              <input
                type="text"
                required
                className="form-control"
                placeholder="e.g. UPI-9988112233 or UTR12345"
                value={newPayment.reference}
                onChange={(e) => setNewPayment({ ...newPayment, reference: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Payment Date</label>
              <input
                type="date"
                required
                className="form-control"
                value={newPayment.payment_date}
                onChange={(e) => setNewPayment({ ...newPayment, payment_date: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Receipt Notes</label>
            <textarea
              rows={2}
              className="form-textarea"
              placeholder="e.g. 20% advance payment received against agreed quotation"
              value={newPayment.notes}
              onChange={(e) => setNewPayment({ ...newPayment, notes: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsRecordOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Verify & Record Payment
            </button>
          </div>
        </form>
      </Modal>

      {/* Official Payment Receipt Modal */}
      <Modal isOpen={isReceiptOpen} onClose={() => setIsReceiptOpen(false)} title="Official Payment Receipt" maxWidth="600px">
        {selectedPayment && (
          <div style={{ padding: '10px' }}>
            <div style={{ textAlign: 'center', borderBottom: '2px solid var(--border-color)', paddingBottom: '16px', marginBottom: '20px' }}>
              <h2 style={{ fontSize: '20px', fontWeight: '800', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
                AARKA SOLAR OPERATIONS
              </h2>
              <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Official Customer Acknowledgment Receipt</p>
              <div style={{ marginTop: '8px', fontSize: '15px', fontWeight: '700' }}>
                Receipt No: {selectedPayment.payment_number}
              </div>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px', fontSize: '13px', marginBottom: '20px' }}>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Received From:</span>
                <div style={{ fontWeight: '700' }}>{selectedPayment.customer_name}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Against Sales Order:</span>
                <div style={{ fontWeight: '700' }}>{selectedPayment.order_number}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Payment Mode:</span>
                <div>{selectedPayment.method}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Transaction Reference:</span>
                <div style={{ fontWeight: '600' }}>{selectedPayment.reference}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Payment Date:</span>
                <div>{selectedPayment.payment_date}</div>
              </div>
              <div>
                <span style={{ color: 'var(--text-muted)' }}>Verification Status:</span>
                <div><StatusBadge status={selectedPayment.verified_status} /></div>
              </div>
            </div>

            <div style={{ backgroundColor: 'var(--color-primary-50)', padding: '16px', borderRadius: '8px', textAlign: 'center', marginBottom: '24px', border: '1px solid var(--color-primary-200)' }}>
              <div style={{ fontSize: '12px', color: 'var(--color-primary-800)', fontWeight: '700', textTransform: 'uppercase' }}>Amount Received</div>
              <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)', marginTop: '2px' }}>
                ₹{selectedPayment.amount?.toLocaleString()}
              </div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button className="btn btn-secondary" onClick={() => window.print()}>
                <Printer size={16} /> Print Receipt
              </button>
              <button className="btn btn-primary" onClick={() => setIsReceiptOpen(false)}>
                Done
              </button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};



export default PaymentsPage;
