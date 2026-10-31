import React, { useState, useEffect } from 'react';
import { Plus, Boxes, AlertTriangle, ArrowUpDown, History, ShieldCheck, Download } from 'lucide-react';
import { inventoryAPI, productsAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { Modal } from '../../components/common/Modal';

export const InventoryPage = () => {
  const [inventory, setInventory] = useState([]);
  const [products, setProducts] = useState([]);
  const [movements, setMovements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('stock'); // 'stock' or 'movements'
  const [lowStockFilter, setLowStockFilter] = useState(false);

  // Modals
  const [isReceiveOpen, setIsReceiveOpen] = useState(false);
  const [isAdjustOpen, setIsAdjustOpen] = useState(false);

  // Forms
  const [receiveData, setReceiveData] = useState({
    product_id: '',
    quantity: 10,
    supplier: 'Waaree Energies Ltd',
    purchase_reference: 'PO-2026-INWARD',
    warehouse_location: 'Main Warehouse - Rack A',
    serial_numbers_text: '',
  });

  const [adjustData, setAdjustData] = useState({
    product_id: '',
    quantity_delta: -1,
    reason: 'Damaged in transit inspection',
  });

  const fetchData = async () => {
    setLoading(true);
    try {
      const [invRes, prodRes, movRes] = await Promise.all([
        inventoryAPI.getInventory({ low_stock_only: lowStockFilter }),
        productsAPI.getProducts(),
        inventoryAPI.getMovements(),
      ]);
      setInventory(invRes.data);
      setProducts(prodRes.data);
      setMovements(movRes.data);
      if (prodRes.data.length > 0) {
        setReceiveData((prev) => ({ ...prev, product_id: prodRes.data[0].id }));
        setAdjustData((prev) => ({ ...prev, product_id: prodRes.data[0].id }));
      }
    } catch (err) {
      console.error('Failed to load inventory:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [lowStockFilter]);

  const handleReceiveStock = async (e) => {
    e.preventDefault();
    try {
      const serials = receiveData.serial_numbers_text
        ? receiveData.serial_numbers_text.split('\n').map((s) => s.trim()).filter(Boolean)
        : [];

      await inventoryAPI.receiveStock({
        product_id: parseInt(receiveData.product_id),
        quantity: parseInt(receiveData.quantity),
        supplier: receiveData.supplier,
        purchase_reference: receiveData.purchase_reference,
        warehouse_location: receiveData.warehouse_location,
        serial_numbers: serials.length > 0 ? serials : undefined,
      });

      setIsReceiveOpen(false);
      fetchData();
      alert('Stock receipt successfully registered and audited!');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to receive stock');
    }
  };

  const handleAdjustStock = async (e) => {
    e.preventDefault();
    try {
      await inventoryAPI.adjustStock({
        product_id: parseInt(adjustData.product_id),
        quantity_delta: parseInt(adjustData.quantity_delta),
        reason: adjustData.reason,
      });
      setIsAdjustOpen(false);
      fetchData();
      alert('Stock adjustment saved.');
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to adjust stock');
    }
  };

  const totalValuation = inventory.reduce((sum, item) => sum + (item.total_valuation || 0), 0);
  const lowStockCount = inventory.filter((item) => item.quantity <= item.reorder_level).length;

  const stockColumns = [
    {
      header: 'Product Name',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '700' }}>{row.product_name}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.sku}</div>
        </div>
      ),
    },
    {
      header: 'Category',
      accessor: 'category',
      render: (row) => <span className="badge badge-neutral">{row.category}</span>,
    },
    {
      header: 'On Hand',
      render: (row) => (
        <span style={{ fontWeight: '700', fontSize: '15px', color: row.quantity <= row.reorder_level ? 'var(--color-rose-600)' : 'var(--text-main)' }}>
          {row.quantity}
        </span>
      ),
    },
    {
      header: 'Reserved',
      accessor: 'reserved_quantity',
      render: (row) => <span style={{ color: 'var(--text-muted)' }}>{row.reserved_quantity}</span>,
    },
    {
      header: 'Available',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-700)' }}>
          {row.available_quantity}
        </span>
      ),
    },
    {
      header: 'Reorder Level',
      accessor: 'reorder_level',
    },
    {
      header: 'Unit Cost',
      render: (row) => <span>₹{row.unit_price?.toLocaleString()}</span>,
    },
    {
      header: 'Valuation (₹)',
      render: (row) => <span style={{ fontWeight: '700' }}>₹{row.total_valuation?.toLocaleString()}</span>,
    },
    {
      header: 'Location',
      accessor: 'warehouse_location',
    },
  ];

  const movementColumns = [
    {
      header: 'Product',
      accessor: 'product_name',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '600' }}>{row.product_name}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{row.sku}</div>
        </div>
      ),
    },
    {
      header: 'Movement Type',
      accessor: 'movement_type',
      render: (row) => <span className="badge badge-info">{row.movement_type}</span>,
    },
    {
      header: 'Quantity Delta',
      render: (row) => (
        <span style={{ fontWeight: '700', color: row.quantity >= 0 ? 'var(--color-primary-700)' : 'var(--color-rose-600)' }}>
          {row.quantity > 0 ? `+${row.quantity}` : row.quantity}
        </span>
      ),
    },
    {
      header: 'Reference Type / ID',
      render: (row) => (
        <div>
          <span style={{ fontSize: '13px', fontWeight: '600' }}>{row.reference_type}</span>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{row.reference_id || '—'}</div>
        </div>
      ),
    },
    {
      header: 'Audit Notes',
      accessor: 'notes',
      render: (row) => <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{row.notes}</span>,
    },
  ];

  return (
    <div>
      {/* Top Banner */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '20px' }}>
        <div className="aarka-card" style={{ padding: '20px' }}>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>
            Total Warehouse Asset Valuation
          </div>
          <div style={{ fontSize: '28px', fontWeight: '800', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)', marginTop: '4px' }}>
            ₹{totalValuation.toLocaleString()}
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-light)', marginTop: '2px' }}>
            Audited PostgreSQL balances across solar panels, inverters, batteries, BOS
          </div>
        </div>

        <div className="aarka-card" style={{ padding: '20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: '12px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>
              Low-Stock Products Alert
            </div>
            <div style={{ fontSize: '28px', fontWeight: '800', color: lowStockCount > 0 ? 'var(--color-rose-600)' : 'var(--color-primary-600)', fontFamily: 'var(--font-display)', marginTop: '4px' }}>
              {lowStockCount} Items
            </div>
            <div style={{ fontSize: '12px', color: 'var(--text-light)', marginTop: '2px' }}>
              Products below configured minimum safety thresholds
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn btn-secondary btn-sm" onClick={() => setIsAdjustOpen(true)}>
              <ArrowUpDown size={14} /> Adjust Stock
            </button>
            <button className="btn btn-primary" onClick={() => setIsReceiveOpen(true)}>
              <Plus size={16} /> Inward Stock
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: '10px', marginBottom: '16px' }}>
        <button
          className={`btn btn-sm ${activeTab === 'stock' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('stock')}
        >
          <Boxes size={14} /> Warehouse Stock Balances
        </button>
        <button
          className={`btn btn-sm ${activeTab === 'movements' ? 'btn-primary' : 'btn-secondary'}`}
          onClick={() => setActiveTab('movements')}
        >
          <History size={14} /> Audit Trail & Movements ({movements.length})
        </button>
      </div>

      {activeTab === 'stock' ? (
        <DataTable
          title="Warehouse Inventory Master"
          subtitle="Real-time physical vs reserved stock balances; Rule #6 strictly prevents negative inventory"
          columns={stockColumns}
          data={inventory}
          searchKey="product_name"
          searchPlaceholder="Search warehouse stock by product name, SKU..."
        />
      ) : (
        <DataTable
          title="Stock Movement Ledger (Audit Trail)"
          subtitle="Immutable transactional movement record for every receipt, dispatch, adjustment and installation"
          columns={movementColumns}
          data={movements}
          searchKey="product_name"
          searchPlaceholder="Filter audit trail..."
        />
      )}

      {/* Inward Stock Modal */}
      <Modal isOpen={isReceiveOpen} onClose={() => setIsReceiveOpen(false)} title="Receive Stock (Goods Inward)">
        <form onSubmit={handleReceiveStock}>
          <div className="form-group">
            <label className="form-label">Product to Receive *</label>
            <select
              className="form-select"
              required
              value={receiveData.product_id}
              onChange={(e) => setReceiveData({ ...receiveData, product_id: e.target.value })}
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku}) {p.requires_serial && '[REQUIRES SERIAL]'}
                </option>
              ))}
            </select>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">Quantity Received *</label>
              <input
                type="number"
                required
                min={1}
                className="form-control"
                value={receiveData.quantity}
                onChange={(e) => setReceiveData({ ...receiveData, quantity: parseInt(e.target.value) || 0 })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Supplier / OEM Vendor</label>
              <input
                type="text"
                className="form-control"
                value={receiveData.supplier}
                onChange={(e) => setReceiveData({ ...receiveData, supplier: e.target.value })}
              />
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
            <div className="form-group">
              <label className="form-label">PO / Delivery Challan Ref</label>
              <input
                type="text"
                className="form-control"
                value={receiveData.purchase_reference}
                onChange={(e) => setReceiveData({ ...receiveData, purchase_reference: e.target.value })}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Warehouse Bin / Location</label>
              <input
                type="text"
                className="form-control"
                value={receiveData.warehouse_location}
                onChange={(e) => setReceiveData({ ...receiveData, warehouse_location: e.target.value })}
              />
            </div>
          </div>

          <div className="form-group">
            <label className="form-label">Serial Numbers (One per line if serialized equipment)</label>
            <textarea
              rows={3}
              className="form-textarea"
              placeholder="INV-3KW-9901&#10;INV-3KW-9902"
              value={receiveData.serial_numbers_text}
              onChange={(e) => setReceiveData({ ...receiveData, serial_numbers_text: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsReceiveOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Verify & Accept Inward
            </button>
          </div>
        </form>
      </Modal>

      {/* Adjust Stock Modal */}
      <Modal isOpen={isAdjustOpen} onClose={() => setIsAdjustOpen(false)} title="Stock Adjustment (Audit Log)">
        <form onSubmit={handleAdjustStock}>
          <div className="form-group">
            <label className="form-label">Product to Adjust *</label>
            <select
              className="form-select"
              required
              value={adjustData.product_id}
              onChange={(e) => setAdjustData({ ...adjustData, product_id: e.target.value })}
            >
              {products.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name} ({p.sku})
                </option>
              ))}
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Quantity Delta (e.g. -2 for damage, +5 for physical audit count) *</label>
            <input
              type="number"
              required
              className="form-control"
              value={adjustData.quantity_delta}
              onChange={(e) => setAdjustData({ ...adjustData, quantity_delta: parseInt(e.target.value) || 0 })}
            />
            <p style={{ fontSize: '11px', color: 'var(--text-light)', marginTop: '4px' }}>
              Enforces Rule #6: Negative stock mutations are strictly rejected by PostgreSQL transaction check.
            </p>
          </div>

          <div className="form-group">
            <label className="form-label">Audit Reason *</label>
            <textarea
              rows={2}
              required
              className="form-textarea"
              placeholder="Reason for stock correction"
              value={adjustData.reason}
              onChange={(e) => setAdjustData({ ...adjustData, reason: e.target.value })}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '16px' }}>
            <button type="button" className="btn btn-secondary" onClick={() => setIsAdjustOpen(false)}>
              Cancel
            </button>
            <button type="submit" className="btn btn-primary">
              Record Adjustment
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
};



export default InventoryPage;
