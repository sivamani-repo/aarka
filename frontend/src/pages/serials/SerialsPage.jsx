import React, { useState, useEffect } from 'react';
import { Plus, Barcode, Search, CheckCircle, AlertCircle, History, Eye, ShieldCheck, Wrench } from 'lucide-react';
import { serialsAPI, productsAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';
import { Modal } from '../../components/common/Modal';

export const SerialsPage = () => {
  const [serials, setSerials] = useState([]);
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);

  // Modals
  const [isRegisterOpen, setIsRegisterOpen] = useState(false);
  const [isScannerOpen, setIsScannerOpen] = useState(false);
  const [isHistoryOpen, setIsHistoryOpen] = useState(false);
  const [serialHistory, setSerialHistory] = useState(null);

  // Forms
  const [newSerial, setNewSerial] = useState({
    product_id: '',
    serial_number: '',
    supplier: 'Growatt New Energy',
    purchase_reference: 'PO-2026-INWARD',
    current_location: 'Warehouse - Rack S1',
  });

  const [scanInput, setScanInput] = useState('');
  const [scanResult, setScanResult] = useState(null);
  const [scanError, setScanError] = useState('');

  const fetchSerials = async () => {
    setLoading(true);
    try {
      const [serRes, prodRes] = await Promise.all([
        serialsAPI.getSerials(),
        productsAPI.getProducts({ requires_serial: true }),
      ]);
      setSerials(serRes.data);
      setProducts(prodRes.data);
      if (prodRes.data.length > 0) {
        setNewSerial((prev) => ({ ...prev, product_id: prodRes.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load serial numbers:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSerials();
  }, []);

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await serialsAPI.registerSerial({
        ...newSerial,
        product_id: parseInt(newSerial.product_id),
      });
      setIsRegisterOpen(false);
      setNewSerial({ ...newSerial, serial_number: '' });
      fetchSerials();
      alert('Serial number successfully registered and indexed.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to register serial');
    }
  };

  const handleScan = async (e) => {
    e.preventDefault();
    setScanResult(null);
    setScanError('');
    if (!scanInput.trim()) return;
    try {
      const res = await serialsAPI.scanSerial({ barcode: scanInput.trim() });
      setScanResult(res.data);
    } catch (err) {
      setScanError(err.response?.data?.detail || 'Serial not found or invalid barcode');
    }
  };

  const openHistory = async (sn) => {
    try {
      const res = await serialsAPI.getSerialHistory(sn);
      setSerialHistory(res.data);
      setIsHistoryOpen(true);
    } catch (err) {
      alert('Failed to load serial history');
    }
  };

  const columns = [
    {
      header: 'Serial Number',
      accessor: 'serial_number',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)', letterSpacing: '0.04em' }}>
          {row.serial_number}
        </span>
      ),
    },
    {
      header: 'Equipment Name',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '600' }}>{row.product_name}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{row.category}</div>
        </div>
      ),
    },
    {
      header: 'Lifecycle Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Assigned Customer / Order',
      render: (row) => (
        <div>
          {row.customer_name ? (
            <div>
              <div style={{ fontWeight: '600' }}>{row.customer_name}</div>
              <div style={{ fontSize: '12px', color: 'var(--color-primary-700)' }}>{row.order_number}</div>
            </div>
          ) : (
            <span style={{ fontSize: '12px', color: 'var(--text-light)' }}>In Warehouse Stock</span>
          )}
        </div>
      ),
    },
    {
      header: 'Current Location',
      accessor: 'current_location',
    },
    {
      header: 'Warranty Span',
      render: (row) => (
        <div style={{ fontSize: '12px' }}>
          {row.warranty_start ? (
            <div>
              <span style={{ color: 'var(--color-primary-700)', fontWeight: '600' }}>Active</span>: {row.warranty_start} to {row.warranty_end}
            </div>
          ) : (
            <span style={{ color: 'var(--text-light)' }}>Starts on delivery</span>
          )}
        </div>
      ),
    },
    {
      header: 'Actions',
      render: (row) => (
        <button className="btn btn-secondary btn-sm" onClick={() => openHistory(row.serial_number)}>
          <History size={13} /> Full History
        </button>
      ),
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginBottom: '20px' }}>
        <button className="btn btn-secondary" onClick={() => setIsScannerOpen(true)}>
          <Barcode size={16} /> Barcode Scanner Simulator
        </button>
        <button className="btn btn-primary" onClick={() => setIsRegisterOpen(true)}>
          <Plus size={16} /> Register Serial Number
        </button>
      </div>

      <DataTable
        title="Serialized Equipment Directory"
        subtitle="MANDATORY RULE #5: Unique serials strictly enforced; Serial cannot be assigned to multiple customers simultaneously"
        columns={columns}
        data={serials}
        searchKey="serial_number"
        searchPlaceholder="Scan or search serial number (e.g. INV-3KW-9001)..."
      />

      {/* Barcode Scanner Modal */}
      <Modal isOpen={isScannerOpen} onClose={() => setIsScannerOpen(false)} title="Barcode Scanner & Allocation Verifier">
        <form onSubmit={handleScan}>
          <div style={{ textAlign: 'center', marginBottom: '16px' }}>
            <Barcode size={44} style={{ margin: '0 auto 8px', color: 'var(--color-primary-700)' }} />
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Supports handheld USB barcode scanners (sends Enter key automatically) or manual input.
            </p>
          </div>

          <div className="form-group">
            <input
              type="text"
              autoFocus
              className="form-control"
              style={{ fontSize: '16px', fontWeight: '700', textAlign: 'center', height: '44px', letterSpacing: '0.05em' }}
              placeholder="SCAN OR TYPE SERIAL NUMBER..."
              value={scanInput}
              onChange={(e) => setScanInput(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', marginBottom: '16px' }}>
            Verify Serial in Database
          </button>
        </form>

        {scanError && (
          <div style={{ padding: '12px', backgroundColor: 'var(--color-rose-50)', color: 'var(--color-rose-600)', borderRadius: '8px', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={16} />
            <span>{scanError}</span>
          </div>
        )}

        {scanResult && (
          <div style={{ backgroundColor: 'var(--color-primary-50)', border: '1px solid var(--color-primary-200)', borderRadius: '8px', padding: '16px', fontSize: '13px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', color: 'var(--color-primary-800)', fontWeight: '700', fontSize: '15px' }}>
              <CheckCircle size={18} /> Verified Serialized Asset
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div><strong>Serial Number:</strong> {scanResult.serial_number}</div>
              <div><strong>Product:</strong> {scanResult.product_name}</div>
              <div><strong>Status:</strong> <StatusBadge status={scanResult.status} /></div>
              <div><strong>Location:</strong> {scanResult.current_location}</div>
            </div>
          </div>
        )}
      </Modal>

      {/* Register Serial Modal */}
      <Modal isOpen={isRegisterOpen} onClose={() => setIsRegisterOpen(false)} title="Register High-Value Serialized Equipment">
        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label className="form-label">Product *</label>
            <select
              className="form-select"
              required
              value={newSerial.product_id}
              onChange={(e) => setNewSerial({ ...newSerial, product_id: e.target.value })}
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Serial Number (Barcoded) *</label>
            <input
              type="text"
              required
              className="form-control"
              placeholder="e.g. INV-3KW-9050 or BAT-150AH-8050"
              value={newSerial.serial_number}
              onChange={(e) => setNewSerial({ ...newSerial, serial_number: e.target.value.toUpperCase() })}
            />
            <p style={{ fontSize: '11px', color: 'var(--text-light)', marginTop: '4px' }}>
              Enforces Rule #5: Duplicates are rejected with a unique database index constraint.
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Supplier / Manufacturer</label>
              <input
                type="text"
                className="form-control"
                value={newSerial.supplier}
                onChange={(e) => setNewSerial({ ...newSerial, supplier: e.target.value })}
              />
            </div>
            <div className="form-group">
              <label className="form-label">Warehouse Location</label>
              <input
                type="text"
                className="form-control"
                value={newSerial.current_location}
                onChange={(e) => setNewSerial({ ...newSerial, current_location: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsRegisterOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Register Serial Asset
            </button>
          </div>
        </form>
      </Modal>

      {/* Cradle-to-Grave Lifecycle History Modal */}
      <Modal isOpen={isHistoryOpen} onClose={() => setIsHistoryOpen(false)} title={`Asset Lifecycle History: ${serialHistory?.serial_number}`} maxWidth="750px">
        {serialHistory && (
          <div>
            <div style={{ backgroundColor: 'var(--bg-subtle)', padding: '16px', borderRadius: '8px', marginBottom: '20px', fontSize: '13px' }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: '700' }}>Equipment</div>
                  <div style={{ fontWeight: '700', fontSize: '15px' }}>{serialHistory.product?.name}</div>
                  <div>SKU: {serialHistory.product?.sku} • {serialHistory.product?.manufacturer}</div>
                </div>
                <div>
                  <div style={{ color: 'var(--text-muted)', fontSize: '11px', textTransform: 'uppercase', fontWeight: '700' }}>Current State & Location</div>
                  <div style={{ marginTop: '2px' }}><StatusBadge status={serialHistory.status} /></div>
                  <div style={{ marginTop: '4px', color: 'var(--text-muted)' }}>{serialHistory.warehouse_location}</div>
                </div>
              </div>
            </div>

            {/* Allocated Order & Customer */}
            <div style={{ marginBottom: '18px' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Customer & Order Allocation
              </div>
              {serialHistory.order ? (
                <div style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: '8px', fontSize: '13px' }}>
                  <div><strong>Customer:</strong> {serialHistory.order.customer_name} ({serialHistory.order.customer_phone})</div>
                  <div><strong>Sales Order:</strong> {serialHistory.order.order_number}</div>
                  <div><strong>Dispatched:</strong> {serialHistory.dispatch_date || 'In Transit'}</div>
                </div>
              ) : (
                <div style={{ fontSize: '12px', color: 'var(--text-light)', padding: '10px', backgroundColor: 'var(--bg-page)', borderRadius: '6px' }}>
                  Not yet allocated to any customer order. Available in warehouse stock.
                </div>
              )}
            </div>

            {/* Active Warranties */}
            <div style={{ marginBottom: '18px' }}>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Warranty Record & Coverage
              </div>
              {(serialHistory.warranties || []).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-light)', padding: '10px', backgroundColor: 'var(--bg-page)', borderRadius: '6px' }}>
                  Warranty will be automatically activated upon warehouse delivery confirmation.
                </div>
              ) : (
                (serialHistory.warranties || []).map((w) => (
                  <div key={w.id} style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: '8px', fontSize: '13px', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong>{w.warranty_number}</strong>
                      <StatusBadge status={w.status} />
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--color-primary-700)', marginTop: '2px' }}>
                      Coverage: {w.start} to {w.end}
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '2px' }}>
                      {w.terms}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Service & Repair History */}
            <div>
              <div style={{ fontSize: '12px', fontWeight: '700', color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '6px' }}>
                Service & Repair Claim History
              </div>
              {(serialHistory.service_tickets || []).length === 0 ? (
                <div style={{ fontSize: '12px', color: 'var(--text-light)', padding: '10px', backgroundColor: 'var(--bg-page)', borderRadius: '6px' }}>
                  Clean operational history. No warranty claims or service tickets logged for this asset.
                </div>
              ) : (
                (serialHistory.service_tickets || []).map((t) => (
                  <div key={t.id} style={{ padding: '12px 16px', border: '1px solid var(--border-color)', borderRadius: '8px', fontSize: '13px', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <strong>{t.ticket_number}</strong>
                      <StatusBadge status={t.status} />
                    </div>
                    <div style={{ marginTop: '2px' }}>Fault: {t.fault}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Reported: {t.reported_date} • Warranty: {t.warranty_status}</div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
};



export default SerialsPage;
