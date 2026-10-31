import React, { useState, useEffect } from 'react';
import { Package, Calculator, Zap, ShieldCheck, Check, Info } from 'lucide-react';
import { productsAPI, bomAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';

export const PackagesPage = () => {
  const [packages, setPackages] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);

  // Interactive BOM Simulator
  const [simPackage, setSimPackage] = useState('On-Grid System');
  const [simCapacity, setSimCapacity] = useState(3.0);
  const [bomResult, setBomResult] = useState(null);
  const [simLoading, setSimLoading] = useState(false);

  const fetchPackagesAndTemplates = async () => {
    setLoading(true);
    try {
      const [pkgRes, tempRes] = await Promise.all([
        productsAPI.getPackages(),
        bomAPI.getTemplates(),
      ]);
      setPackages(pkgRes.data);
      setTemplates(tempRes.data);
    } catch (err) {
      console.error('Failed to load packages:', err);
    } finally {
      setLoading(false);
    }
  };

  const runBOMSimulation = async (pkgType, cap) => {
    setSimLoading(true);
    try {
      const res = await bomAPI.calculateBOM(pkgType, cap);
      setBomResult(res.data);
    } catch (err) {
      console.error('Failed to simulate BOM:', err);
    } finally {
      setSimLoading(false);
    }
  };

  useEffect(() => {
    fetchPackagesAndTemplates();
    runBOMSimulation(simPackage, simCapacity);
  }, []);

  const handleSimulate = (pkgType, cap) => {
    setSimPackage(pkgType);
    setSimCapacity(cap);
    runBOMSimulation(pkgType, cap);
  };

  return (
    <div>
      {/* Interactive BOM Calculator Card */}
      <div className="aarka-card" style={{ marginBottom: '28px', border: '1px solid var(--color-primary-200)', boxShadow: 'var(--shadow-sm)' }}>
        <div className="aarka-card-header" style={{ backgroundColor: 'var(--color-primary-50)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Calculator size={20} color="var(--color-primary-700)" />
            <div>
              <h3 style={{ fontSize: '17px', fontWeight: '700', color: 'var(--color-primary-900)' }}>
                Automated Bill of Materials (BOM) Recipe Engine
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--color-primary-700)' }}>
                Configurable component ratios across 1kW to 5kW capacities and On-Grid / Off-Grid topologies
              </p>
            </div>
          </div>
        </div>

        <div className="aarka-card-body">
          {/* Controls */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '24px' }}>
            <div>
              <label className="form-label">Package Architecture</label>
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {['On-Grid System', 'Off-Grid System', 'Solar Panel Set', 'Installation Service'].map((type) => (
                  <button
                    key={type}
                    type="button"
                    className={`btn btn-sm ${simPackage === type ? 'btn-primary' : 'btn-secondary'}`}
                    onClick={() => handleSimulate(type, simCapacity)}
                  >
                    {type}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="form-label">Solar System Capacity</label>
              <div style={{ display: 'flex', gap: '8px' }}>
                {[1.0, 2.0, 3.0, 4.0, 5.0].map((cap) => (
                  <button
                    key={cap}
                    type="button"
                    className={`btn btn-sm ${simCapacity === cap ? 'btn-accent' : 'btn-secondary'}`}
                    onClick={() => handleSimulate(simPackage, cap)}
                  >
                    {cap} kW {cap === 3.0 && '★'}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* BOM Breakdown Display */}
          {simLoading ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)' }}>
              Calculating hardware recipes and pricing...
            </div>
          ) : bomResult ? (
            <div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))', gap: '14px', marginBottom: '20px' }}>
                <div style={{ padding: '14px', backgroundColor: 'var(--bg-subtle)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Hardware Cost</div>
                  <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-main)', marginTop: '2px' }}>
                    ₹{bomResult.hardware_cost?.toLocaleString()}
                  </div>
                </div>
                <div style={{ padding: '14px', backgroundColor: 'var(--bg-subtle)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Installation & Testing</div>
                  <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-main)', marginTop: '2px' }}>
                    ₹{bomResult.installation_cost?.toLocaleString()}
                  </div>
                </div>
                <div style={{ padding: '14px', backgroundColor: 'var(--bg-subtle)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>Subtotal (Excl Tax)</div>
                  <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-main)', marginTop: '2px' }}>
                    ₹{bomResult.subtotal?.toLocaleString()}
                  </div>
                </div>
                <div style={{ padding: '14px', backgroundColor: 'var(--bg-subtle)', borderRadius: '8px' }}>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: '700' }}>GST (18%)</div>
                  <div style={{ fontSize: '20px', fontWeight: '800', color: 'var(--text-main)', marginTop: '2px' }}>
                    ₹{bomResult.tax_amount?.toLocaleString()}
                  </div>
                </div>
                <div style={{ padding: '14px', backgroundColor: 'var(--color-primary-50)', borderRadius: '8px', border: '1px solid var(--color-primary-200)' }}>
                  <div style={{ fontSize: '11px', color: 'var(--color-primary-800)', textTransform: 'uppercase', fontWeight: '700' }}>Grand Total</div>
                  <div style={{ fontSize: '22px', fontWeight: '800', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)', marginTop: '2px' }}>
                    ₹{bomResult.grand_total?.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Itemized Table */}
              <table className="aarka-table">
                <thead>
                  <tr>
                    <th>Component Name</th>
                    <th>Category</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total Price</th>
                    <th>Serialized?</th>
                  </tr>
                </thead>
                <tbody>
                  {(bomResult.components || []).map((item, idx) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: '600' }}>{item.product_name}</td>
                      <td><span className="badge badge-neutral">{item.category}</span></td>
                      <td><strong>{item.quantity}</strong> {item.unit}</td>
                      <td>₹{item.unit_price?.toLocaleString()}</td>
                      <td style={{ fontWeight: '700' }}>₹{item.total_price?.toLocaleString()}</td>
                      <td>
                        {item.is_serialized ? (
                          <span className="badge badge-warning">Track Serial</span>
                        ) : (
                          <span style={{ fontSize: '12px', color: 'var(--text-light)' }}>Standard</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : null}
        </div>
      </div>

      {/* Configured Packages Catalog */}
      <div className="aarka-card">
        <div className="aarka-card-header">
          <div>
            <h3 style={{ fontSize: '17px', fontWeight: '700' }}>Standard Package Master List</h3>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Configured retail packages for salespeople and automated quotations</p>
          </div>
        </div>
        <div className="aarka-card-body" style={{ padding: 0 }}>
          <table className="aarka-table">
            <thead>
              <tr>
                <th>Package Name</th>
                <th>Type</th>
                <th>Capacity</th>
                <th>Base Package Price</th>
                <th>Description</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {packages.map((pkg) => (
                <tr key={pkg.id}>
                  <td style={{ fontWeight: '700', color: 'var(--color-primary-900)' }}>{pkg.name}</td>
                  <td><span className="badge badge-neutral">{pkg.package_type}</span></td>
                  <td><strong>{pkg.capacity_kw} kW</strong></td>
                  <td style={{ fontWeight: '700', color: 'var(--color-primary-700)' }}>
                    ₹{pkg.base_price?.toLocaleString()}
                  </td>
                  <td style={{ fontSize: '13px', color: 'var(--text-muted)' }}>{pkg.description}</td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleSimulate(pkg.package_type, pkg.capacity_kw)}
                    >
                      Inspect BOM
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};



export default PackagesPage;
