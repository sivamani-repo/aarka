import React, { useState, useEffect } from 'react';
import { Plus, Send, CheckCircle, FileText, Eye, Printer, ShoppingCart, AlertCircle } from 'lucide-react';
import { quotationsAPI, customersAPI, surveysAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const QuotationsPage = () => {
  const [quotations, setQuotations] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [approvedSurveys, setApprovedSurveys] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [isViewOpen, setIsViewOpen] = useState(false);
  const [selectedQuote, setSelectedQuote] = useState(null);
  const [orderCreatedMsg, setOrderCreatedMsg] = useState('');

  // Form
  const [newQuote, setNewQuote] = useState({
    customer_id: '',
    survey_id: '',
    package_type: 'On-Grid System',
    capacity_kw: 3.0,
    discount: 0,
    advance_percentage: 20,
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [qRes, custRes, survRes] = await Promise.all([
        quotationsAPI.getQuotations(),
        customersAPI.getCustomers(),
        surveysAPI.getSurveys({ approval_status: 'APPROVED' }),
      ]);
      setQuotations(qRes.data);
      setCustomers(custRes.data);
      setApprovedSurveys(survRes.data);
      if (custRes.data.length > 0) {
        setNewQuote((prev) => ({ ...prev, customer_id: custRes.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load quotations:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleCreateQuotation = async (e) => {
    e.preventDefault();
    try {
      const res = await quotationsAPI.createQuotation({
        ...newQuote,
        customer_id: parseInt(newQuote.customer_id),
        survey_id: newQuote.survey_id ? parseInt(newQuote.survey_id) : null,
        capacity_kw: parseFloat(newQuote.capacity_kw),
        discount: parseFloat(newQuote.discount) || 0,
        advance_percentage: parseFloat(newQuote.advance_percentage) || 20,
      });
      setIsCreateOpen(false);
      fetchData();
      // Auto open the created quotation for inspection
      setSelectedQuote(res.data);
      setIsViewOpen(true);
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to create quotation');
    }
  };

  const handleSendQuotation = async (quoteId) => {
    try {
      await quotationsAPI.sendQuotation(quoteId);
      fetchData();
    } catch (err) {
      alert('Failed to send quotation');
    }
  };

  const handleAcceptQuotation = async (quoteId) => {
    try {
      const res = await quotationsAPI.acceptQuotation(quoteId);
      setOrderCreatedMsg(`✓ Quotation accepted! Sales Order ${res.data.order_number} automatically generated with picklist and snapshot pricing.`);
      fetchData();
      if (selectedQuote && selectedQuote.id === quoteId) {
        setSelectedQuote({ ...selectedQuote, status: 'ACCEPTED' });
      }
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to accept quotation');
    }
  };

  const openQuoteDetail = (quote) => {
    setSelectedQuote(quote);
    setOrderCreatedMsg('');
    setIsViewOpen(true);
  };

  const columns = [
    {
      header: 'Quote Number',
      accessor: 'quotation_number',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
          {row.quotation_number}
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
      header: 'Package & Capacity',
      render: (row) => (
        <div>
          <span style={{ fontWeight: '600' }}>{row.capacity_kw} kW</span> • {row.package_type}
        </div>
      ),
    },
    {
      header: 'Grand Total (₹)',
      render: (row) => (
        <span style={{ fontWeight: '800', color: 'var(--text-main)' }}>
          ₹{row.total_amount?.toLocaleString()}
        </span>
      ),
    },
    {
      header: 'Advance Required',
      render: (row) => (
        <span style={{ fontSize: '13px', color: 'var(--color-amber-600)', fontWeight: '600' }}>
          ₹{row.advance_amount?.toLocaleString()}
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
          <button className="btn btn-secondary btn-sm" onClick={() => openQuoteDetail(row)}>
            <Eye size={13} /> View
          </button>
          {row.status === 'DRAFT' && (
            <button className="btn btn-secondary btn-sm" onClick={() => handleSendQuotation(row.id)}>
              <Send size={13} /> Send
            </button>
          )}
          {(row.status === 'DRAFT' || row.status === 'SENT') && (
            <button className="btn btn-primary btn-sm" onClick={() => handleAcceptQuotation(row.id)}>
              <CheckCircle size={13} /> Customer Accept
            </button>
          )}
        </div>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '20px' }}>
        <button className="btn btn-primary" onClick={() => setIsCreateOpen(true)}>
          <Plus size={16} /> Generate Automated Quotation
        </button>
      </div>

      <DataTable
        title="Quotation Management"
        subtitle="MANDATORY RULE: BOM recipes calculated on backend; Customer acceptance creates Sales Order"
        columns={columns}
        data={quotations}
        searchKey="quotation_number"
        searchPlaceholder="Search quotations by number, customer..."
      />

      {/* Generate Quotation Modal */}
      <Modal isOpen={isCreateOpen} onClose={() => setIsCreateOpen(false)} title="Generate Solar Quotation with Automated BOM">
        <form onSubmit={handleCreateQuotation}>
          <div className="form-group">
            <label className="form-label">Select Customer *</label>
            <select
              className="form-select"
              required
              value={newQuote.customer_id}
              onChange={(e) => setNewQuote({ ...newQuote, customer_id: e.target.value })}
            >
              {customers.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name} ({c.phone}) - {c.address}
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Approved Site Survey (Mandatory for Final Quotes)</label>
            <select
              className="form-select"
              value={newQuote.survey_id}
              onChange={(e) => setNewQuote({ ...newQuote, survey_id: e.target.value })}
            >
              <option value="">-- Select Approved Site Survey (or leave blank for preliminary draft) --</option>
              {approvedSurveys.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.survey_reference} - {s.customer_name} ({s.roof_area} sqft, {s.roof_direction})
                </option>
              ))}
            </select>
            <p style={{ fontSize: '11px', color: 'var(--text-light)', marginTop: '4px' }}>
              Enforces Rule #1: If a site survey is specified, engineering approval is strictly verified by the backend.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Package Type</label>
              <select
                className="form-select"
                value={newQuote.package_type}
                onChange={(e) => setNewQuote({ ...newQuote, package_type: e.target.value })}
              >
                <option value="On-Grid System">On-Grid System (Net Metering)</option>
                <option value="Off-Grid System">Off-Grid System (With Battery)</option>
                <option value="Solar Panel Set">Solar Panel Set Only</option>
                <option value="Installation Service">Installation Service Only</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">System Capacity (kW)</label>
              <select
                className="form-select"
                value={newQuote.capacity_kw}
                onChange={(e) => setNewQuote({ ...newQuote, capacity_kw: parseFloat(e.target.value) })}
              >
                <option value={1.0}>1 kW</option>
                <option value={2.0}>2 kW</option>
                <option value={3.0}>3 kW [Standard Residential]</option>
                <option value={4.0}>4 kW</option>
                <option value={5.0}>5 kW</option>
              </select>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Commercial Discount (₹)</label>
              <input
                type="number"
                className="form-control"
                value={newQuote.discount}
                onChange={(e) => setNewQuote({ ...newQuote, discount: parseFloat(e.target.value) || 0 })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Advance Payment Requirement (%)</label>
              <input
                type="number"
                className="form-control"
                value={newQuote.advance_percentage}
                onChange={(e) => setNewQuote({ ...newQuote, advance_percentage: parseFloat(e.target.value) || 20 })}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsCreateOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Calculate BOM & Generate Quotation
            </button>
          </div>
        </form>
      </Modal>

      {/* Printable Quotation View Modal */}
      <Modal isOpen={isViewOpen} onClose={() => setIsViewOpen(false)} title={`Quotation Document: ${selectedQuote?.quotation_number}`} maxWidth="850px">
        {selectedQuote && (
          <div>
            {orderCreatedMsg && (
              <div style={{ padding: '12px 16px', backgroundColor: 'var(--color-primary-50)', color: 'var(--color-primary-800)', borderRadius: 'var(--radius-md)', marginBottom: '16px', fontSize: '13px', fontWeight: '600', border: '1px solid var(--color-primary-200)' }}>
                {orderCreatedMsg}
              </div>
            )}

            {/* Header / Brand in Quote */}
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid var(--color-primary-800)', paddingBottom: '16px', marginBottom: '20px' }}>
              <div>
                <h2 style={{ fontSize: '22px', fontWeight: '800', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>AARKA SOLAR</h2>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Solar Operations, Simplified. • GSTIN: 36AAACA1234F1Z5</p>
                <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Hyderabad, Telangana • Support: +91 40 2345 6789</p>
              </div>

              <div style={{ textAlign: 'right' }}>
                <div style={{ fontSize: '18px', fontWeight: '800', color: 'var(--text-main)' }}>{selectedQuote.quotation_number}</div>
                <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Date: {new Date().toISOString().split('T')[0]}</div>
                <div style={{ marginTop: '4px' }}><StatusBadge status={selectedQuote.status} /></div>
              </div>
            </div>

            {/* Customer Details */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', backgroundColor: 'var(--bg-subtle)', padding: '14px 18px', borderRadius: '8px', marginBottom: '20px', fontSize: '13px' }}>
              <div>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '700' }}>Prepared For:</div>
                <div style={{ fontWeight: '700', fontSize: '14px' }}>{selectedQuote.customer_name}</div>
                <div>{selectedQuote.customer_phone}</div>
                <div style={{ color: 'var(--text-muted)' }}>{selectedQuote.customer_address}</div>
              </div>
              <div>
                <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: '700' }}>System Specification:</div>
                <div style={{ fontWeight: '700', fontSize: '14px' }}>{selectedQuote.capacity_kw} kW {selectedQuote.package_type}</div>
                <div>System Topology: {selectedQuote.system_type}</div>
                <div style={{ color: 'var(--color-primary-700)', fontWeight: '600' }}>20-Year Panel / 2-Year Inverter Warranty</div>
              </div>
            </div>

            {/* Itemized BOM Table */}
            <div style={{ marginBottom: '20px' }}>
              <div style={{ fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', color: 'var(--text-muted)', marginBottom: '8px' }}>
                Itemized Bill of Materials & Service Scope
              </div>
              <table className="aarka-table">
                <thead>
                  <tr>
                    <th>#</th>
                    <th>Component / Description</th>
                    <th>Qty</th>
                    <th>Unit Price</th>
                    <th style={{ textAlign: 'right' }}>Amount (₹)</th>
                  </tr>
                </thead>
                <tbody>
                  {(selectedQuote.items || []).map((it, idx) => (
                    <tr key={idx}>
                      <td>{idx + 1}</td>
                      <td>
                        <div style={{ fontWeight: '600' }}>{it.product_name}</div>
                        <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{it.sku || it.category}</div>
                      </td>
                      <td>{it.quantity} {it.unit}</td>
                      <td>₹{it.unit_price?.toLocaleString()}</td>
                      <td style={{ textAlign: 'right', fontWeight: '700' }}>₹{it.total_price?.toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Financial Summary */}
            <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '24px' }}>
              <div style={{ width: '320px', fontSize: '13px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                  <span>Hardware Subtotal:</span>
                  <span>₹{selectedQuote.hardware_cost?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                  <span>Installation & Testing:</span>
                  <span>₹{selectedQuote.installation_cost?.toLocaleString()}</span>
                </div>
                {selectedQuote.discount > 0 && (
                  <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', color: 'var(--color-primary-700)' }}>
                    <span>Special Discount:</span>
                    <span>-₹{selectedQuote.discount?.toLocaleString()}</span>
                  </div>
                )}
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0' }}>
                  <span>GST Tax (18%):</span>
                  <span>₹{selectedQuote.tax_amount?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderTop: '2px solid var(--text-main)', fontSize: '16px', fontWeight: '800' }}>
                  <span>Grand Total:</span>
                  <span style={{ color: 'var(--color-primary-800)' }}>₹{selectedQuote.total_amount?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', backgroundColor: 'var(--color-primary-50)', padding: '6px 8px', borderRadius: '4px', fontWeight: '600' }}>
                  <span>Required Advance (20%):</span>
                  <span style={{ color: 'var(--color-primary-700)' }}>₹{selectedQuote.advance_amount?.toLocaleString()}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 8px', color: 'var(--text-muted)' }}>
                  <span>Balance Payable:</span>
                  <span>₹{selectedQuote.balance_amount?.toLocaleString()}</span>
                </div>
              </div>
            </div>

            {/* Terms and Conditions */}
            <div style={{ padding: '12px 16px', backgroundColor: 'var(--bg-subtle)', borderRadius: '8px', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '20px' }}>
              <div style={{ fontWeight: '700', marginBottom: '4px', color: 'var(--text-main)' }}>Standard Terms & Conditions:</div>
              <pre style={{ fontFamily: 'inherit', whiteSpace: 'pre-wrap', lineHeight: 1.5 }}>
                {selectedQuote.terms_conditions}
              </pre>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <button className="btn btn-secondary" onClick={() => window.print()}>
                <Printer size={16} /> Print / Save PDF
              </button>

              <div style={{ display: 'flex', gap: '10px' }}>
                {selectedQuote.status === 'DRAFT' && (
                  <button className="btn btn-secondary" onClick={() => handleSendQuotation(selectedQuote.id)}>
                    <Send size={16} /> Mark as Sent to Customer
                  </button>
                )}
                {selectedQuote.status !== 'ACCEPTED' && (
                  <button className="btn btn-primary" onClick={() => handleAcceptQuotation(selectedQuote.id)}>
                    <CheckCircle size={16} /> Customer Accepted (Create Sales Order)
                  </button>
                )}
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};


export default QuotationsPage;
