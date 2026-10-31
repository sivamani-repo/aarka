import React from 'react';
import { useLocation } from 'react-router-dom';
import { LogOut } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

export const Topbar = () => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const firstName = user?.name?.trim()?.[0] || 'A';

  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/': return 'Director Operations Dashboard';
      case '/leads': return 'Customer & Lead Pipeline';
      case '/customers': return 'Customer Master Directory';
      case '/surveys': return 'Site Survey & Roof Inspections';
      case '/packages': return 'Configured Solar Packages';
      case '/quotations': return 'Automated Quotations & BOM';
      case '/orders': return 'Sales Orders & Picklists';
      case '/payments': return 'Customer Payments & Receivables';
      case '/inventory': return 'Warehouse Inventory Management';
      case '/serials': return 'Serial Number & Barcode Tracking';
      case '/dispatch': return 'Warehouse Dispatch & Logistics';
      case '/technicians': return 'Technician Force & Profiles';
      case '/schedule': return 'Field Operations Scheduling';
      case '/installations': return 'Installation Jobs & Handover';
      case '/warranties': return 'Automated Warranty Tracking';
      case '/service': return 'After-Sales Service & Repairs';
      case '/suppliers': return 'Suppliers & OEM Vendors';
      case '/finance': return 'Finance & Project Profitability';
      case '/subsidies': return 'Government Subsidy Management';
      case '/reports': return 'Director Reports & CSV Export';
      case '/team': return 'Team & Role Administration';
      case '/settings': return 'System Settings & Policies';
      default: return 'AARKA Solar System';
    }
  };

  return (
    <header
      style={{
        height: '64px',
        backgroundColor: '#ffffff',
        borderBottom: '1px solid var(--border-color)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 32px',
        flexShrink: 0,
      }}
    >
      <div>
        <h2 style={{ fontSize: '18px', fontWeight: '700', color: 'var(--text-main)', letterSpacing: '-0.01em' }}>
          {getPageTitle(location.pathname)}
        </h2>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
        {/* Live Database status pill */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            backgroundColor: 'var(--color-primary-50)',
            color: 'var(--color-primary-700)',
            padding: '5px 10px',
            borderRadius: 'var(--radius-full)',
            fontSize: '12px',
            fontWeight: '600',
            border: '1px solid var(--color-primary-200)',
          }}
        >
          <span
            style={{
              width: '7px',
              height: '7px',
              borderRadius: '50%',
              backgroundColor: '#10b981',
              boxShadow: '0 0 6px #10b981',
            }}
          />
          <span>PostgreSQL Active (aarka_db)</span>
        </div>

        {/* User Profile & Role */}
        {user && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '13px', fontWeight: '700', color: 'var(--text-main)' }}>
                {user.name}
              </div>
              <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                {user.role}
                {user.department ? ` · ${user.department}` : ''}
                {user.employee_id ? ` · ${user.employee_id}` : ''}
              </div>
            </div>

            <div
              style={{
                width: '36px',
                height: '36px',
                borderRadius: '50%',
                backgroundColor: 'var(--color-primary-800)',
                color: '#ffffff',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '700',
                fontSize: '14px',
              }}
            >
              {firstName.toUpperCase()}
            </div>

            <button
              onClick={logout}
              title="Sign Out"
              style={{
                background: 'none',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '6px',
                display: 'flex',
                alignItems: 'center',
                borderRadius: 'var(--radius-sm)',
              }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'var(--color-rose-600)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'var(--text-muted)')}
            >
              <LogOut size={18} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
};



export default Topbar;
