import React, { useState, useEffect } from 'react';
import { Search, ShieldCheck, AlertCircle, Clock, CheckCircle, Barcode, Calendar } from 'lucide-react';
import { warrantiesAPI } from '../../services/api';
import { DataTable } from '../../components/common/DataTable';
import { StatusBadge } from '../../components/common/StatusBadge';

export const WarrantiesPage = () => {
  const [warranties, setWarranties] = useState([]);
  const [loading, setLoading] = useState(true);

  // Search Tool
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState(null);
  const [searchLoading, setSearchLoading] = useState(false);

  const fetchWarranties = async () => {
    setLoading(true);
    try {
      const res = await warrantiesAPI.getWarranties();
      setWarranties(res.data);
    } catch (err) {
      console.error('Failed to load warranties:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWarranties();
  }, []);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) {
      setSearchResults(null);
      return;
    }
    setSearchLoading(true);
    try {
      const res = await warrantiesAPI.searchWarranties(searchQuery.trim());
      setSearchResults(res.data.results);
    } catch (err) {
      console.error('Failed to search warranty:', err);
    } finally {
      setSearchLoading(false);
    }
  };

  const columns = [
    {
      header: 'Warranty Ref',
      accessor: 'warranty_number',
      render: (row) => (
        <span style={{ fontWeight: '700', color: 'var(--color-primary-800)', fontFamily: 'var(--font-display)' }}>
          {row.warranty_number || 'WAR-AUTO'}
        </span>
      ),
    },
    {
      header: 'Serial Number',
      accessor: 'serial_number',
      render: (row) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Barcode size={14} color="var(--color-amber-600)" />
          <strong style={{ letterSpacing: '0.04em' }}>{row.serial_number}</strong>
        </div>
      ),
    },
    {
      header: 'Product & Category',
      render: (row) => (
        <div>
          <div style={{ fontWeight: '600' }}>{row.product_name}</div>
          <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{row.category}</div>
        </div>
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
      header: 'Warranty Start',
      accessor: 'warranty_start',
    },
    {
      header: 'Warranty Expiry',
      accessor: 'warranty_end',
    },
    {
      header: 'Coverage Status',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Coverage Terms',
      accessor: 'coverage_terms',
      render: (row) => (
        <span style={{ fontSize: '12px', color: 'var(--text-muted)', maxWidth: '240px', display: 'inline-block' }}>
          {row.coverage_terms}
        </span>
      ),
    },
  ];

  return (
    <div>
      {/* Quick Warranty Verification Search Tool */}
      <div className="aarka-card" style={{ marginBottom: '24px', backgroundColor: '#0c2318', color: '#ffffff', padding: '24px 28px' }}>
        <div style={{ maxWidth: '700px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#a7e4c2', fontSize: '13px', fontWeight: '700', textTransform: 'uppercase', marginBottom: '8px' }}>
            <ShieldCheck size={18} /> Instant Equipment Warranty Verification Tool
          </div>
          <h2 style={{ fontSize: '20px', fontWeight: '800', marginBottom: '14px', fontFamily: 'var(--font-display)' }}>
            Search by Serial Number, Customer Name, or Phone
          </h2>

          <form onSubmit={handleSearch} style={{ display: 'flex', gap: '10px' }}>
            <div style={{ position: 'relative', flex: 1 }}>
              <Search size={18} style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: '#7ba08d' }} />
              <input
                type="text"
                placeholder="Enter Serial Number (e.g. INV-3KW-8888 or INV-3KW-9001)..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  padding: '12px 14px 12px 42px',
                  backgroundColor: '#163827',
                  border: '1px solid #23533a',
                  borderRadius: 'var(--radius-md)',
                  color: '#ffffff',
                  fontSize: '14px',
                  outline: 'none',
                }}
              />
            </div>
            <button type="submit" className="btn btn-accent" disabled={searchLoading}>
              {searchLoading ? 'Checking...' : 'Check Warranty'}
            </button>
          </form>
        </div>

        {/* Live Search Results Pill View */}
        {searchResults && (
          <div style={{ marginTop: '20px', backgroundColor: '#133524', padding: '16px', borderRadius: '8px', border: '1px solid #23533a' }}>
            {searchResults.length === 0 ? (
              <div style={{ color: '#fca5a5', fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <AlertCircle size={16} /> No registered warranty found matching '{searchQuery}'.
              </div>
            ) : (
              <div>
                <div style={{ fontSize: '12px', color: '#a7e4c2', fontWeight: '700', marginBottom: '8px' }}>
                  Verification Result ({searchResults.length} Match):
                </div>
                {searchResults.map((res, idx) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 14px', backgroundColor: '#0c2318', borderRadius: '6px', fontSize: '13px' }}>
                    <div>
                      <span style={{ fontWeight: '700', color: '#ffffff', letterSpacing: '0.04em' }}>{res.serial_number}</span> • {res.product_name}
                      <div style={{ fontSize: '11px', color: '#94bca7' }}>
                        Customer: {res.customer_name} ({res.customer_phone}) • Valid: {res.warranty_start} to {res.warranty_end}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <StatusBadge status={res.status} />
                      <div style={{ fontSize: '11px', color: '#78c59f', marginTop: '2px' }}>
                        {res.days_remaining} days remaining
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      <DataTable
        title="Automated Warranty Certificates"
        subtitle="CRITICAL RULE #8: Automatically activated upon recorded delivery date (Inverter: 2 yrs, Battery: 2 yrs, Panels: 20 yrs)"
        columns={columns}
        data={warranties}
        searchKey="serial_number"
        searchPlaceholder="Filter warranties by serial number, customer..."
      />
    </div>
  );
};



export default WarrantiesPage;
